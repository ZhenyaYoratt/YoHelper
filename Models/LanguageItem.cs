namespace YoHelper.Models
{
    public class LanguageItem
    {
        public string Code { get; set; } = "";
        public string Display { get; set; } = "";
        public LanguageItem() { }
        public LanguageItem(string code, string display)
        {
            Code = code;
            Display = display;
        }

        public override string ToString() => Display;
    }
}
