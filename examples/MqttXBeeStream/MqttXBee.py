from serial_grabber.reader.Xbee import MessageVerifier


class XBeeMessageVerifier(MessageVerifier):
    def verify_message(self, transaction):
        try:
            data = transaction.split("\n")
            print len("\n".join(data[1:-2])), int(data[-2])

            if int(data[-2]) == len("\n".join(data[1:-2])):
                return True, "OK"
            else:
                raise ValueError()
        except ValueError, e:
            return False, "NA"

