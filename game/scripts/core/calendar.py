class Calendar:
    def __init__(self):
        self.current_day = 1
        self.current_month = 1
        self.current_year = 1
        self.day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.month_names = ["January", "February", "March", "April", "May", "June", 
                          "July", "August", "September", "October", "November", "December"]
    
    def get_current_date(self):
        return {
            "day": self.current_day,
            "month": self.current_month,
            "year": self.current_year,
            "day_name": self.day_names[(self.current_day - 1) % 7],
            "month_name": self.month_names[self.current_month - 1]
        }
    
    def advance_day(self):
        self.current_day += 1
        if self.current_day > 7:  # Assuming 7 days per week
            self.current_day = 1
            self.current_month += 1
            if self.current_month > 12:
                self.current_month = 1
                self.current_year += 1 