
class Datapoint:
    def __init__(self, datetime_value, value):
        self.meas_time = datetime_value
        self.value = value
        self.value_unc = 0.0


class Datacouple:
    def __init__(self, datetime_value, ref_value, cmp_value):
        self.meas_time = datetime_value
        self.ref_value = ref_value
        self.cmp_value = cmp_value
        self.ratio_ref_cmp = ref_value / cmp_value if cmp_value and ref_value else None

        self.ref_value_unc = 0
        self.cmp_value_unc = 0
        self.ratio_unc = None


class Interval:
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time
        self.meas_time = self.start_time + (self.end_time - self.start_time) / 2

