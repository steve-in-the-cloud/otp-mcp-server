#
# MIT License
#
# Copyright (c) 2025 Stephen Ujfalussy
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
HTTP-based MCP server compatible with Zendesk's OAuth flow.
Similar to Atlassian's MCP implementation at https://mcp.atlassian.com/v1/mcp
"""

import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from .server import get_token_db, init_token_db
from .tool import calculate_otp_codes, add_token, delete_token, find_tokens, format_token

__all__ = ["create_app", "run_server"]

# OAuth tokens storage (in-memory for now)
_oauth_tokens: Dict[str, Dict[str, Any]] = {}

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))

    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "service": "otp-mcp-server"})

    @app.route("/oauth/authorize", methods=["GET"])
    def oauth_authorize():
        """
        OAuth authorization endpoint.
        Zendesk redirects user here to grant access.
        """
        client_id = request.args.get("client_id")
        redirect_uri = request.args.get("redirect_uri")
        state = request.args.get("state")
        scope = request.args.get("scope", "read write")

        if not client_id or not redirect_uri:
            return jsonify({"error": "invalid_request", "error_description": "Missing required parameters"}), 400

        # Generate authorization code
        auth_code = secrets.token_urlsafe(32)

        # Store authorization code temporarily (5 minutes)
        _oauth_tokens[auth_code] = {
            "type": "authorization_code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
        }

        # Redirect back to Zendesk with auth code
        redirect_url = f"{redirect_uri}?code={auth_code}"
        if state:
            redirect_url += f"&state={state}"

        return f"""
        <html>
            <head><title>OTP MCP Authorization</title></head>
            <body>
                <h1>OTP MCP Server Authorization</h1>
                <p>Authorize Zendesk to access your OTP tokens?</p>
                <p><a href="{redirect_url}">Grant Access</a></p>
            </body>
        </html>
        """

    @app.route("/oauth/token", methods=["POST"])
    def oauth_token():
        """
        OAuth token endpoint.
        Exchanges authorization code for access token.
        """
        grant_type = request.form.get("grant_type") or request.json.get("grant_type")

        if grant_type == "authorization_code":
            code = request.form.get("code") or request.json.get("code")

            if not code or code not in _oauth_tokens:
                return jsonify({"error": "invalid_grant", "error_description": "Invalid authorization code"}), 400

            auth_data = _oauth_tokens.pop(code)

            # Check expiration
            if datetime.utcnow() > auth_data["expires_at"]:
                return jsonify({"error": "invalid_grant", "error_description": "Authorization code expired"}), 400

            # Generate access token
            access_token = secrets.token_urlsafe(48)
            refresh_token = secrets.token_urlsafe(48)

            _oauth_tokens[access_token] = {
                "type": "access_token",
                "client_id": auth_data["client_id"],
                "scope": auth_data["scope"],
                "expires_at": datetime.utcnow() + timedelta(hours=1),
                "refresh_token": refresh_token,
            }

            _oauth_tokens[refresh_token] = {
                "type": "refresh_token",
                "client_id": auth_data["client_id"],
                "scope": auth_data["scope"],
                "access_token": access_token,
            }

            return jsonify({
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": refresh_token,
                "scope": auth_data["scope"],
            })

        elif grant_type == "refresh_token":
            refresh_token = request.form.get("refresh_token") or request.json.get("refresh_token")

            if not refresh_token or refresh_token not in _oauth_tokens:
                return jsonify({"error": "invalid_grant", "error_description": "Invalid refresh token"}), 400

            refresh_data = _oauth_tokens[refresh_token]

            # Generate new access token
            new_access_token = secrets.token_urlsafe(48)

            _oauth_tokens[new_access_token] = {
                "type": "access_token",
                "client_id": refresh_data["client_id"],
                "scope": refresh_data["scope"],
                "expires_at": datetime.utcnow() + timedelta(hours=1),
                "refresh_token": refresh_token,
            }

            # Update refresh token reference
            _oauth_tokens[refresh_token]["access_token"] = new_access_token

            return jsonify({
                "access_token": new_access_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": refresh_token,
                "scope": refresh_data["scope"],
            })

        return jsonify({"error": "unsupported_grant_type"}), 400

    def verify_access_token() -> Optional[Dict[str, Any]]:
        """Verify OAuth access token from Authorization header."""
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix

        if token not in _oauth_tokens:
            return None

        token_data = _oauth_tokens[token]

        if token_data["type"] != "access_token":
            return None

        # Check expiration
        if datetime.utcnow() > token_data["expires_at"]:
            _oauth_tokens.pop(token, None)
            return None

        return token_data

    @app.route("/v1/mcp", methods=["POST", "GET"])
    @app.route("/mcp", methods=["POST", "GET"])
    def mcp_endpoint():
        """
        Main MCP endpoint - handles JSON-RPC requests.
        Compatible with Zendesk's MCP integration.
        """
        # Verify OAuth token
        token_data = verify_access_token()
        if not token_data:
            return jsonify({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32001,
                    "message": "Unauthorized",
                    "data": {"description": "Valid OAuth access token required"}
                }
            }), 401

        if request.method == "GET":
            # Return server capabilities
            return jsonify({
                "name": "otp-mcp-server",
                "version": "0.3.0",
                "description": "OTP (One-Time Password) MCP Server",
                "capabilities": {
                    "tools": True,
                    "resources": True,
                },
                "transport": "http",
            })

        # Handle JSON-RPC POST requests
        try:
            rpc_request = request.get_json()
        except Exception:
            return jsonify({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }), 400

        if not rpc_request or "method" not in rpc_request:
            return jsonify({
                "jsonrpc": "2.0",
                "id": rpc_request.get("id") if rpc_request else None,
                "error": {"code": -32600, "message": "Invalid Request"}
            }), 400

        method = rpc_request["method"]
        params = rpc_request.get("params", {})
        request_id = rpc_request.get("id", 1)

        try:
            # Handle MCP protocol methods
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "otp-mcp-server",
                        "version": "0.3.0"
                    },
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                    }
                }

            elif method == "tools/list":
                result = {
                    "tools": [
                        {
                            "name": "list_otp_tokens",
                            "description": "Returns the list of OTP tokens",
                            "inputSchema": {"type": "object", "properties": {}}
                        },
                        {
                            "name": "get_details",
                            "description": "Get details of OTP tokens matching pattern",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"pattern": {"type": "string", "description": "Token pattern"}},
                                "required": ["pattern"]
                            }
                        },
                        {
                            "name": "calculate_otp_codes",
                            "description": "Calculate OTP codes for tokens matching pattern",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"pattern": {"type": "string", "description": "Token pattern"}},
                                "required": ["pattern"]
                            }
                        },
                        {
                            "name": "add_token",
                            "description": "Add a new OTP token",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "secret": {"type": "string", "description": "Base32 secret key"},
                                    "issuer": {"type": "string", "description": "Issuer name"},
                                    "account": {"type": "string", "description": "Account name"},
                                    "type": {"type": "string", "enum": ["TOTP", "HOTP"], "default": "TOTP"},
                                    "algorithm": {"type": "string", "enum": ["SHA1", "SHA256", "SHA512", "MD5"]},
                                    "digits": {"type": "integer", "default": 6},
                                    "period": {"type": "integer", "default": 30}
                                },
                                "required": ["secret", "issuer", "account"]
                            }
                        },
                        {
                            "name": "delete_token",
                            "description": "Delete OTP token matching pattern",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"pattern": {"type": "string", "description": "Token pattern"}},
                                "required": ["pattern"]
                            }
                        }
                    ]
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})

                if tool_name == "list_otp_tokens":
                    db = get_token_db()
                    tokens_list = db.get_tokens()
                    if not tokens_list:
                        result = {"content": [{"type": "text", "text": "No OTP tokens found."}]}
                    else:
                        text = "\n".join([f"{x.rowid}# {x}" for x in tokens_list])
                        result = {"content": [{"type": "text", "text": text}]}

                elif tool_name == "get_details":
                    pattern = tool_args.get("pattern", "")
                    tokens_list = find_tokens(pattern)
                    if not tokens_list:
                        result = {"content": [{"type": "text", "text": "No OTP tokens found."}], "isError": True}
                    else:
                        text = "\n---\n".join([format_token(x) for x in tokens_list])
                        result = {"content": [{"type": "text", "text": text}]}

                elif tool_name == "calculate_otp_codes":
                    pattern = tool_args.get("pattern", "")
                    codes = []
                    tokens = find_tokens(pattern)
                    for token in tokens:
                        try:
                            otp = token.calculate()
                            codes.append(f"{token.rowid}# {str(token)} {otp}")
                        except Exception as e:
                            result = {
                                "content": [{"type": "text", "text": f"Error generating OTP: {str(e)}"}],
                                "isError": True
                            }
                            break
                    else:
                        if not codes:
                            result = {"content": [{"type": "text", "text": "No OTP tokens found."}], "isError": True}
                        else:
                            result = {"content": [{"type": "text", "text": "\n".join(codes)}]}

                elif tool_name == "add_token":
                    try:
                        from freakotp.secret import Secret
                        from freakotp.token import Token, TokenType

                        db = get_token_db()
                        token = Token(
                            uri=None,
                            type=TokenType[tool_args.get("type", "TOTP")],
                            algorithm=tool_args.get("algorithm", "SHA1"),
                            counter=tool_args.get("counter", 0),
                            digits=tool_args.get("digits", 6),
                            issuer=tool_args["issuer"],
                            issuer_int=None,
                            issuer_ext=None,
                            label=tool_args["account"],
                            period=tool_args.get("period", 30),
                            secret=Secret.from_base32(tool_args["secret"]),
                            token_db=db,
                        )
                        db.insert(token)
                        result = {"content": [{"type": "text", "text": "Token added successfully."}]}
                    except Exception as e:
                        result = {
                            "content": [{"type": "text", "text": f"Error adding token: {str(e)}"}],
                            "isError": True
                        }

                elif tool_name == "delete_token":
                    pattern = tool_args.get("pattern", "")
                    if not pattern:
                        result = {
                            "content": [{"type": "text", "text": "Pattern cannot be empty."}],
                            "isError": True
                        }
                    else:
                        db = get_token_db()
                        tokens = find_tokens(pattern)
                        if not tokens:
                            result = {
                                "content": [{"type": "text", "text": "No OTP tokens found."}],
                                "isError": True
                            }
                        else:
                            for token in tokens:
                                db.delete(token)
                            result = {"content": [{"type": "text", "text": f"{len(tokens)} tokens deleted."}]}

                else:
                    result = {
                        "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                        "isError": True
                    }

            elif method == "resources/list":
                result = {"resources": []}

            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }), 404

            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            })

        except Exception as e:
            logger.exception("Error handling MCP request")
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": "Server error",
                    "data": {"description": str(e)}
                }
            }), 500

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        """Handle HTTP exceptions."""
        return jsonify({
            "error": e.name,
            "message": e.description,
        }), e.code

    @app.errorhandler(Exception)
    def handle_error(e):
        """Handle all other exceptions."""
        logger.exception("Unhandled exception")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
        }), 500

    return app


def run_server(host: str = "0.0.0.0", port: int = 8000, db_path: str = None):
    """Run the HTTP MCP server."""
    if db_path:
        init_token_db(db_path)

    app = create_app()
    app.run(host=host, port=port, debug=False)
