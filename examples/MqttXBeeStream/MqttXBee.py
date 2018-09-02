import logging

from serial_grabber.reader import MessageVerifier


class XBeeMessageVerifier(MessageVerifier):
    logger = logging.getLogger("MessageVerifier")
    def verify_message(self, transaction):
        try:
            data = transaction.split("\n")
            if int(data[-2]) == len("\n".join(data[1:-2])):
                return True, "OK"
            else:
                self.logger.error("Reported length: %s, Actual length: %s"%(int(data[-2]), len("\n".join(data[1:-2]))))
                raise ValueError()
        except ValueError, e:
            self.logger.error("Could not convert %s to an integer."%data[-2])
            return False, "NA"

