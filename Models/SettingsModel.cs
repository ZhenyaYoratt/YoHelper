namespace YoHelper.Models
{
    public class AppSettings
    {
        // "Default" | "Light" | "Dark"
        public string Theme { get; set; } = "Default";

        // "" or null = system default; otherwise e.g. "ru-RU", "en-US"
        public string Language { get; set; } = "";
    }

}
