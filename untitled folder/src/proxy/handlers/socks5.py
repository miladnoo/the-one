"""
SOCKS5 proxy handler implementation
"""

import asyncio
import logging
import socket
import struct
from typing import Dict, Any, Tuple, Optional

from ..auth import authenticate_user


class Socks5ProxyHandler:
    """
    Handler for SOCKS5 proxy requests.
    """
    
    # SOCKS5 protocol constants
    VERSION = 0x05
    
    # Authentication methods
    NO_AUTH = 0x00
    USERNAME_PASSWORD = 0x02
    NO_ACCEPTABLE_METHODS = 0xFF
    
    # Commands
    CONNECT = 0x01
    BIND = 0x02
    UDP_ASSOCIATE = 0x03
    
    # Address types
    IPV4 = 0x01
    DOMAIN = 0x03
    IPV6 = 0x04
    
    # Reply codes
    SUCCEEDED = 0x00
    GENERAL_FAILURE = 0x01
    CONNECTION_NOT_ALLOWED = 0x02
    NETWORK_UNREACHABLE = 0x03
    HOST_UNREACHABLE = 0x04
    CONNECTION_REFUSED = 0x05
    TTL_EXPIRED = 0x06
    COMMAND_NOT_SUPPORTED = 0x07
    ADDRESS_TYPE_NOT_SUPPORTED = 0x08
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SOCKS5 proxy handler.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.require_auth = config['proxy']['socks5'].get('require_auth', False)
    
    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handle a SOCKS5 client connection.
        
        Args:
            reader: Stream reader for the client connection
            writer: Stream writer for the client connection
        """
        try:
            # Perform the SOCKS5 handshake
            if not await self._handshake(reader, writer):
                return
            
            # Process the client request
            await self._process_request(reader, writer)
        except Exception as e:
            self.logger.error(f"Error handling SOCKS5 connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _handshake(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> bool:
        """
        Perform the SOCKS5 handshake.
        
        Args:
            reader: Stream reader for the client connection
            writer: Stream writer for the client connection
            
        Returns:
            True if the handshake was successful, False otherwise
        """
        # Read the client greeting
        try:
            version, nmethods = struct.unpack('!BB', await reader.readexactly(2))
        except asyncio.IncompleteReadError:
            self.logger.error("Failed to read SOCKS5 greeting")
            return False
        
        if version != self.VERSION:
            self.logger.error(f"Unsupported SOCKS version: {version}")
            writer.write(struct.pack('!BB', self.VERSION, self.NO_ACCEPTABLE_METHODS))
            await writer.drain()
            return False
        
        # Read the authentication methods supported by the client
        methods = await reader.readexactly(nmethods)
        
        # Select an authentication method
        if self.require_auth and self.USERNAME_PASSWORD in methods:
            # Username/password authentication
            writer.write(struct.pack('!BB', self.VERSION, self.USERNAME_PASSWORD))
            await writer.drain()
            
            # Perform username/password authentication
            if not await self._authenticate(reader, writer):
                return False
        elif self.NO_AUTH in methods and not self.require_auth:
            # No authentication required
            writer.write(struct.pack('!BB', self.VERSION, self.NO_AUTH))
            await writer.drain()
        else:
            # No acceptable authentication methods
            self.logger.error("No acceptable authentication methods")
            writer.write(struct.pack('!BB', self.VERSION, self.NO_ACCEPTABLE_METHODS))
            await writer.drain()
            return False
        
        return True
    
    async def _authenticate(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> bool:
        """
        Perform username/password authentication.
        
        Args:
            reader: Stream reader for the client connection
            writer: Stream writer for the client connection
            
        Returns:
            True if authentication was successful, False otherwise
        """
        try:
            # Read the authentication request
            ver = await reader.readexactly(1)
            if ver[0] != 0x01:
                self.logger.error(f"Unsupported auth version: {ver[0]}")
                writer.write(struct.pack('!BB', 0x01, 0x01))  # Failure
                await writer.drain()
                return False
            
            # Read username
            ulen = await reader.readexactly(1)
            username = await reader.readexactly(ulen[0])
            
            # Read password
            plen = await reader.readexactly(1)
            password = await reader.readexactly(plen[0])
            
            # Authenticate
            username_str = username.decode('utf-8')
            password_str = password.decode('utf-8')
            
            if authenticate_user(self.config, username_str, password_str):
                writer.write(struct.pack('!BB', 0x01, 0x00))  # Success
                await writer.drain()
                return True
            else:
                writer.write(struct.pack('!BB', 0x01, 0x01))  # Failure
                await writer.drain()
                return False
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            writer.write(struct.pack('!BB', 0x01, 0x01))  # Failure
            await writer.drain()
            return False
    
    async def _process_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Process a SOCKS5 client request.
        
        Args:
            reader: Stream reader for the client connection
            writer: Stream writer for the client connection
        """
        try:
            # Read the request header
            version, cmd, rsv, atyp = struct.unpack('!BBBB', await reader.readexactly(4))
            
            if version != self.VERSION:
                self.logger.error(f"Unsupported SOCKS version: {version}")
                await self._send_reply(writer, self.GENERAL_FAILURE)
                return
            
            # Get the destination address
            if atyp == self.IPV4:
                # IPv4 address
                addr = socket.inet_ntop(socket.AF_INET, await reader.readexactly(4))
            elif atyp == self.DOMAIN:
                # Domain name
                length = (await reader.readexactly(1))[0]
                addr = (await reader.readexactly(length)).decode('utf-8')
            elif atyp == self.IPV6:
                # IPv6 address
                addr = socket.inet_ntop(socket.AF_INET6, await reader.readexactly(16))
            else:
                self.logger.error(f"Unsupported address type: {atyp}")
                await self._send_reply(writer, self.ADDRESS_TYPE_NOT_SUPPORTED)
                return
            
            # Get the destination port
            port = struct.unpack('!H', await reader.readexactly(2))[0]
            
            # Handle the command
            if cmd == self.CONNECT:
                await self._handle_connect(reader, writer, addr, port)
            elif cmd == self.BIND:
                await self._handle_bind(reader, writer, addr, port)
            elif cmd == self.UDP_ASSOCIATE:
                await self._handle_udp_associate(reader, writer, addr, port)
            else:
                self.logger.error(f"Unsupported command: {cmd}")
                await self._send_reply(writer, self.COMMAND_NOT_SUPPORTED)
        except Exception as e:
            self.logger.error(f"Error processing SOCKS5 request: {e}")
            await self._send_reply(writer, self.GENERAL_FAILURE)
    
    async def _handle_connect(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: str, port: int):
        """
        Handle a CONNECT command.
        
        Args:
            reader: Stream reader for the client connection
            writer: Stream writer for the client connection
            addr: Destination address
            port: Destination port
        """
        try:
            # Connect to the destination
            self.logger.info(f"Connecting to {addr}:{port}")
            dest_reader, dest_writer = await asyncio.open_connection(addr, port)
            
            # Send success reply
            local_addr, local_port = writer.get_extra_info('sockname')
            await self._send_reply(writer, self.SUCCEEDED, local_addr, local_port)
            
            # Start forwarding data in both directions
            await self._forward_data(reader, writer, dest_reader, dest_writer)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger.error(f"Error handling CONNECT: {e}")
            await self._send_reply(writer, self.GENERAL_FAILURE)
    
    async def _handle_bind(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: str, port: int):
        """
        Handle a BIND command.
        
        Args:
            reader: Stream reader for the client connection
            writer: Stream writer for the client connection
            addr: Destination address
            port: Destination port
        """
        # BIND is not implemented
        await self._send_reply(writer, self.COMMAND_NOT_SUPPORTED)
    
    async def _handle_udp_associate(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: str, port: int):
        """
        Handle a UDP_ASSOCIATE command.
        
        Args:
            reader: Stream reader for the client connection
            writer: Stream writer for the client connection
            addr: Destination address
            port: Destination port
        """
        # UDP_ASSOCIATE is not implemented
        await self._send_reply(writer, self.COMMAND_NOT_SUPPORTED)
    
    async def _send_reply(self, writer: asyncio.StreamWriter, reply_code: int, bind_addr: str = '0.0.0.0', bind_port: int = 0):
        """
        Send a reply to the client.
        
        Args:
            writer: Stream writer for the client connection
            reply_code: Reply code
            bind_addr: Bind address
            bind_port: Bind port
        """
        try:
            # Convert the bind address to bytes
            if ':' in bind_addr:
                # IPv6
                atyp = self.IPV6
                addr_bytes = socket.inet_pton(socket.AF_INET6, bind_addr)
            else:
                # IPv4
                atyp = self.IPV4
                addr_bytes = socket.inet_pton(socket.AF_INET, bind_addr)
            
            # Build the reply
            reply = struct.pack('!BBBB', self.VERSION, reply_code, 0x00, atyp) + addr_bytes + struct.pack('!H', bind_port)
            
            # Send the reply
            writer.write(reply)
            await writer.drain()
        except Exception as e:
            self.logger.error(f"Error sending reply: {e}")
    
    async def _forward_data(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
        dest_reader: asyncio.StreamReader,
        dest_writer: asyncio.StreamWriter
    ):
        """
        Forward data between the client and the destination.
        
        Args:
            client_reader: Stream reader for the client connection
            client_writer: Stream writer for the client connection
            dest_reader: Stream reader for the destination connection
            dest_writer: Stream writer for the destination connection
        """
        # Create tasks for forwarding data in both directions
        client_to_dest = asyncio.create_task(self._forward(client_reader, dest_writer, 'client -> dest'))
        dest_to_client = asyncio.create_task(self._forward(dest_reader, client_writer, 'dest -> client'))
        
        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [client_to_dest, dest_to_client],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel the pending task
        for task in pending:
            task.cancel()
        
        # Close the destination connection
        dest_writer.close()
        await dest_writer.wait_closed()
    
    async def _forward(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, direction: str):
        """
        Forward data from a reader to a writer.
        
        Args:
            reader: Stream reader
            writer: Stream writer
            direction: Direction of data flow (for logging)
        """
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except Exception as e:
            self.logger.error(f"Error forwarding data ({direction}): {e}")
        finally:
            writer.close()
