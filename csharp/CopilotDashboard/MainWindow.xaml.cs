using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Windows;
using System.Windows.Input;
using System.Windows.Threading;

namespace CopilotDashboard;

public partial class MainWindow : Window
{
    private readonly HttpClient _http = new() { BaseAddress = new Uri("http://127.0.0.1:8765") };
    private readonly DispatcherTimer _timer = new() { Interval = TimeSpan.FromMilliseconds(500) };

    public MainWindow()
    {
        InitializeComponent();
        _timer.Tick += async (_, _) => await RefreshStatusAsync();
        _timer.Start();
        Loaded += async (_, _) => await RefreshStatusAsync();
    }

    private async Task RefreshStatusAsync()
    {
        try
        {
            var status = await _http.GetFromJsonAsync<StatusResponse>("/status");
            if (status is null) return;
            BridgeStatusText.Text = status.bridge_connected ? "Connected" : "Disconnected";
            ProfileText.Text = status.aircraft_profile ?? "—";
            PhaseText.Text = status.phase ?? "—";
            PendingText.Text = status.pending_confirmation ?? "None";

            var wanted = new[] { "ias_kts", "altitude_ft", "radio_alt_ft", "ground_speed_mps", "gear_handle", "flap_ratio" };
            StateText.Text = string.Join(Environment.NewLine,
                wanted.Where(k => status.state?.ContainsKey(k) == true)
                      .Select(k => $"{k,-18} {status.state![k]:0.###}"));
        }
        catch (Exception ex)
        {
            BridgeStatusText.Text = "API unavailable";
            AppendLog($"Status error: {ex.Message}");
        }
    }

    private async Task SendCommandAsync(bool confirm = false)
    {
        var text = CommandText.Text.Trim();
        if (confirm && string.IsNullOrEmpty(text)) text = "confirm";
        if (string.IsNullOrEmpty(text)) return;

        try
        {
            var response = await _http.PostAsJsonAsync("/command", new { text, confirm });
            var json = await response.Content.ReadAsStringAsync();
            var result = JsonSerializer.Deserialize<CommandResponse>(json);
            AppendLog($"> {text}\n{result?.message ?? json}");
            if (!confirm) CommandText.Clear();
            await RefreshStatusAsync();
        }
        catch (Exception ex)
        {
            AppendLog($"Command error: {ex.Message}");
        }
    }

    private void AppendLog(string line)
    {
        LogText.AppendText($"[{DateTime.Now:HH:mm:ss}] {line}{Environment.NewLine}");
        LogText.ScrollToEnd();
    }

    private async void Send_Click(object sender, RoutedEventArgs e) => await SendCommandAsync();
    private async void Confirm_Click(object sender, RoutedEventArgs e) => await SendCommandAsync(confirm: true);

    private async void CommandText_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter)
        {
            e.Handled = true;
            await SendCommandAsync();
        }
    }
}

public sealed class StatusResponse
{
    public bool bridge_connected { get; set; }
    public string? bridge_error { get; set; }
    public string? aircraft_profile { get; set; }
    public string? phase { get; set; }
    public Dictionary<string, double>? state { get; set; }
    public string? pending_confirmation { get; set; }
}

public sealed class CommandResponse
{
    public bool accepted { get; set; }
    public string? action { get; set; }
    public string? message { get; set; }
    public string? command { get; set; }
}
