from datetime import datetime, timezone
import re


class Parser():
    def __init__(self, file_str):
        self.file_str = file_str


    def order_channels(main_list, channel_list):
        # Normalize to lowercase for comparison
        main_list_lower = [channel.lower() for channel in main_list]
        channel_list_lower = [channel.lower() for channel in channel_list]
        
        # Channels found in both lists, ordered by main_list
        ordered_channels = [channel for channel in main_list if channel in channel_list]

        # Channels in channel_list that are not in main_list
        additional_channels = [channel for channel in channel_list if channel not in main_list]
        if additional_channels:
            print(f"Additional channels not used: {additional_channels}")

        # Combine the two lists
        return ordered_channels
    
    @classmethod
    def make_date_obj(cls, date_time):
        """Helper function to create a stdlib datetime object
        :param date_time: string representation of the date and time the EEG was recorded
        :return: stdlib datetime object
        |
        """
        pattern = re.compile(r"(\d+)\D*([-/.])(\d+)[-/.](\d+) (.*)")
        match = pattern.match(date_time)
        if match is None:
            return
        else:
            field1, sep, field2, year, time = match.groups()
            field1 = int(field1)
            field2 = int(field2)
            year = int(year)
            if sep == "." and field2 <= 12: #Some Deymed files have a datetime string format as DD.MM.YYYY
                day = field1
                month = field2
            elif sep == "." and field1 <= 12: #If the first condition failed, the month and day must have been flipped. This is an error that needs to be addressed by the Deymed system.
                day = field2
                month = field1
            elif (sep == r"/" or sep == "-") and field1 <= 12:
                month = field1
                day = field2
            elif sep == "-" and field1 > 1000: #This covers the date format used by Neuromed
                day = year
                year = field1
                month = field2
            elif (sep == r"/" or sep == "-") and field2 <= 12:
                month = field2
                day = field1
            else:
                return None
            d_t = datetime(year, month, day)

            pattern_time = re.compile(r"^(\d+)\D(\d+)\D(\d+)$")
            match_time = pattern_time.match(time)
            if match_time:
                hour, minute, second = match_time.groups()
                d_t = d_t.replace(
                    hour=int(hour), minute=int(minute), second=int(second)
                )

        d_t = d_t.replace(
            tzinfo=timezone.utc
        )  # current version 0.2 of MNE requires time zone info, will remove
        return d_t