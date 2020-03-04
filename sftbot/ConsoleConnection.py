from . import AbstractConnection
import sys


class ConsoleConnection(AbstractConnection.AbstractConnection):
    def __init__(self, name, loglevel):
        """
        just store the encoding.
        """
        super(ConsoleConnection, self).__init__(name, loglevel)

    def _openConnection(self):
        """
        there is nothing to open; all we need is stdout/stdin.
        """
        return True

    def _initConnection(self):
        """
        nothing to do here either.
        """
        return True

    # no need to overload _postConnect either.

    def _closeConnection(self):
        """
        closing is a no-op, too.
        """
        return True

    def _listen(self):
        """
        read data from stdin, and interpret it as a chat message
        """
        try:
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            self._log("keyboard interrupt", 1)
            self._invokeTextCallback("console", "Goodbye.")
            return False

        self._invokeTextCallback("console", line)
        return True

    # send the given line to stdout.
    def _sendMessageUnsafe(self, message):
        """
        write the message to stdout
        """
        print(message)
        return True

    # pass the given line to _sendMessage.
    def _sendTextMessageUnsafe(self, message):
        """
        text messages are just written as they are, no need to add a header
        """
        return self._sendMessage(message)
