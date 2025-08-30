using System;
namespace YoHelper.Pages.Modules.ProcessMonitor
{
    public class LogEntry
    {
        public DateTime Timestamp { get; set; }
        public string Type { get; set; }
        public string Message { get; set; }
        public string FormattedTimestamp => Timestamp.ToString("yyyy-MM-dd HH:mm:ss");

        public LogEntry() { Timestamp = DateTime.Now; }
    }
}
