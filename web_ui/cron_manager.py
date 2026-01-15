"""Cron Manager - Handle crontab operations for notification scheduling."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from crontab import CronTab


# Prefix for all our cron job comments to identify them
CRON_COMMENT_PREFIX = "discord-notifier:"


@dataclass
class CronJobInfo:
    """Information about a cron job."""
    
    enabled: bool
    schedule: Optional[str] = None  # Cron expression like "0 9 * * *"
    schedule_human: Optional[str] = None  # Human readable like "Daily at 9:00 AM"
    next_run: Optional[datetime] = None
    command: Optional[str] = None


# Common schedule presets
SCHEDULE_PRESETS = {
    "daily_9am": {"cron": "0 9 * * *", "label": "Daily at 9:00 AM"},
    "daily_8am": {"cron": "0 8 * * *", "label": "Daily at 8:00 AM"},
    "daily_10am": {"cron": "0 10 * * *", "label": "Daily at 10:00 AM"},
    "daily_noon": {"cron": "0 12 * * *", "label": "Daily at 12:00 PM"},
    "daily_6pm": {"cron": "0 18 * * *", "label": "Daily at 6:00 PM"},
    "weekdays_9am": {"cron": "0 9 * * 1-5", "label": "Weekdays at 9:00 AM"},
    "weekly_monday_9am": {"cron": "0 9 * * 1", "label": "Mondays at 9:00 AM"},
    "weekly_friday_5pm": {"cron": "0 17 * * 5", "label": "Fridays at 5:00 PM"},
}


class CronManager:
    """Manages cron jobs for discord notifications."""

    def __init__(self, user: Optional[str] = None):
        """Initialize the cron manager.
        
        Args:
            user: Username for crontab. None for current user.
        """
        self.user = user
        
    def _get_cron(self) -> CronTab:
        """Get the CronTab instance."""
        if self.user:
            return CronTab(user=self.user)
        return CronTab(user=True)  # Current user

    def _get_comment(self, config_name: str) -> str:
        """Get the cron comment for a config."""
        return f"{CRON_COMMENT_PREFIX}{config_name}"

    def _find_job(self, config_name: str) -> Optional[object]:
        """Find the cron job for a config.
        
        Args:
            config_name: Config file name without .yaml extension.
            
        Returns:
            CronItem or None if not found.
        """
        cron = self._get_cron()
        comment = self._get_comment(config_name)
        
        for job in cron.find_comment(comment):
            return job
        
        return None

    def get_job_status(self, config_name: str) -> CronJobInfo:
        """Get the status of a notification's cron job.
        
        Args:
            config_name: Config file name without .yaml extension.
            
        Returns:
            CronJobInfo with job details.
        """
        job = self._find_job(config_name)
        
        if job is None:
            return CronJobInfo(enabled=False)
        
        # Get schedule info
        schedule = str(job.slices)
        
        # Try to get next run time
        next_run = None
        try:
            schedule_obj = job.schedule(date_from=datetime.now())
            next_run = schedule_obj.get_next()
        except Exception:
            pass
        
        # Generate human-readable schedule
        schedule_human = self._schedule_to_human(schedule)
        
        return CronJobInfo(
            enabled=job.is_enabled(),
            schedule=schedule,
            schedule_human=schedule_human,
            next_run=next_run,
            command=str(job.command),
        )

    def _schedule_to_human(self, cron_expr: str) -> str:
        """Convert a cron expression to human-readable format.
        
        Args:
            cron_expr: Cron expression like "0 9 * * *"
            
        Returns:
            Human-readable string like "Daily at 9:00 AM"
        """
        # Check presets first
        for preset in SCHEDULE_PRESETS.values():
            if preset["cron"] == cron_expr:
                return preset["label"]
        
        # Basic parsing for common patterns
        parts = cron_expr.split()
        if len(parts) != 5:
            return cron_expr
        
        minute, hour, dom, month, dow = parts
        
        try:
            hour_int = int(hour)
            minute_int = int(minute)
            time_str = datetime.strptime(f"{hour_int}:{minute_int}", "%H:%M").strftime("%I:%M %p")
        except ValueError:
            time_str = f"{hour}:{minute}"
        
        if dom == "*" and month == "*":
            if dow == "*":
                return f"Daily at {time_str}"
            elif dow == "1-5":
                return f"Weekdays at {time_str}"
            elif dow == "0,6":
                return f"Weekends at {time_str}"
            else:
                days = {
                    "0": "Sundays", "1": "Mondays", "2": "Tuesdays",
                    "3": "Wednesdays", "4": "Thursdays", "5": "Fridays", "6": "Saturdays"
                }
                if dow in days:
                    return f"{days[dow]} at {time_str}"
        
        return f"At {time_str} ({cron_expr})"

    def get_all_notification_jobs(self) -> dict[str, CronJobInfo]:
        """Get all discord-notifier cron jobs.
        
        Returns:
            Dict mapping config names to their job info.
        """
        cron = self._get_cron()
        jobs = {}
        
        for job in cron:
            comment = job.comment
            if comment and comment.startswith(CRON_COMMENT_PREFIX):
                config_name = comment[len(CRON_COMMENT_PREFIX):]
                
                next_run = None
                try:
                    schedule_obj = job.schedule(date_from=datetime.now())
                    next_run = schedule_obj.get_next()
                except Exception:
                    pass
                
                schedule = str(job.slices)
                
                jobs[config_name] = CronJobInfo(
                    enabled=job.is_enabled(),
                    schedule=schedule,
                    schedule_human=self._schedule_to_human(schedule),
                    next_run=next_run,
                    command=str(job.command),
                )
        
        return jobs

    def enable_notification(self, config_name: str, command: str, schedule: str = "0 9 * * *") -> bool:
        """Enable or update a notification's cron job.
        
        Args:
            config_name: Config file name without .yaml extension.
            command: Full command to run the notifier.
            schedule: Cron schedule expression.
            
        Returns:
            True if successful.
        """
        cron = self._get_cron()
        comment = self._get_comment(config_name)
        
        # Find existing job or create new one
        job = None
        for existing in cron.find_comment(comment):
            job = existing
            break
        
        if job is None:
            job = cron.new(command=command, comment=comment)
        else:
            job.set_command(command)
        
        # Set schedule
        job.setall(schedule)
        job.enable()
        
        cron.write()
        return True

    def disable_notification(self, config_name: str) -> bool:
        """Disable a notification by removing its cron job.
        
        Args:
            config_name: Config file name without .yaml extension.
            
        Returns:
            True if successful (or job didn't exist).
        """
        cron = self._get_cron()
        comment = self._get_comment(config_name)
        
        # Remove all jobs with this comment
        cron.remove_all(comment=comment)
        cron.write()
        
        return True

    def update_schedule(self, config_name: str, schedule: str) -> bool:
        """Update the schedule for an existing cron job.
        
        Args:
            config_name: Config file name without .yaml extension.
            schedule: New cron schedule expression.
            
        Returns:
            True if successful, False if job doesn't exist.
        """
        job = self._find_job(config_name)
        
        if job is None:
            return False
        
        cron = self._get_cron()
        for existing in cron.find_comment(self._get_comment(config_name)):
            existing.setall(schedule)
        
        cron.write()
        return True

    @staticmethod
    def get_schedule_presets() -> dict:
        """Get available schedule presets."""
        return SCHEDULE_PRESETS

