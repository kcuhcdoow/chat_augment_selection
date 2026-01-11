using System;
using System.IO;
using System.Text.Json;
using System.Windows.Forms;
using System.Threading.Tasks;

namespace PollerSettingsGUI
{
    public partial class MainForm : Form
    {
        public MainForm()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            this.Text = "Poller Settings";
            this.Width = 450; // Increased width by 50%
            this.Height = 250;
            this.BackColor = System.Drawing.ColorTranslator.FromHtml("#332a8b");

            // Styling
            this.StartPosition = FormStartPosition.CenterScreen;
            this.Font = new System.Drawing.Font("Arial", 10, System.Drawing.FontStyle.Regular);
            this.ForeColor = System.Drawing.Color.White;

            // Enable Rerolls Checkbox
            CheckBox enableRerolls = new CheckBox();
            enableRerolls.Text = "Enable Rerolls";
            enableRerolls.Top = 20;
            enableRerolls.Left = 20;
            this.Controls.Add(enableRerolls);

            // Rerolls Hint Label
            Label rerollsHint = new Label();
            rerollsHint.Text = "Polls chat in intervals for 1/4 of the duration.";
            rerollsHint.Top = 45;
            rerollsHint.Left = 40;
            rerollsHint.Width = 300;
            rerollsHint.Visible = false;
            enableRerolls.CheckedChanged += (sender, e) =>
            {
                rerollsHint.Visible = enableRerolls.Checked;
            };
            this.Controls.Add(rerollsHint);

            // Timer Duration Label
            Label timerLabel = new Label();
            timerLabel.Text = "Timer Duration (seconds):";
            timerLabel.Top = 75;
            timerLabel.Left = 20;
            this.Controls.Add(timerLabel);

            // Timer Duration TextBox
            TextBox timerInput = new TextBox();
            timerInput.Top = 95;
            timerInput.Left = 20;
            timerInput.Width = 100;
            timerInput.Text = "30"; // Default value
            this.Controls.Add(timerInput);

            // Error Label
            Label errorLabel = new Label();
            errorLabel.Text = "";
            errorLabel.Top = 125;
            errorLabel.Left = 20;
            errorLabel.ForeColor = System.Drawing.Color.Red;
            errorLabel.Width = 240;
            this.Controls.Add(errorLabel);

            // Confirm Button
            Button confirmButton = new Button();
            confirmButton.Text = "Confirm";
            confirmButton.Top = 155;
            confirmButton.Left = 20;
            confirmButton.Width = 80;
            confirmButton.Click += (sender, e) =>
            {
                errorLabel.Text = "";

                if (!int.TryParse(timerInput.Text, out int timer) || timer <= 0)
                {
                    errorLabel.Text = "Timer duration must be a positive number.";
                    return;
                }

                try
                {
                    // Run the poll request in a separate thread to avoid freezing the GUI
                    Task.Run(() =>
                    {
                        using (var client = new System.Net.Http.HttpClient())
                        {
                            var content = new System.Net.Http.StringContent(
                                $"{{\"duration\": {timer}, \"enable_rerolls\": {enableRerolls.Checked.ToString().ToLower()} }}",
                                System.Text.Encoding.UTF8,
                                "application/json"
                            );

                            var response = client.PostAsync("http://127.0.0.1:5000/start_poll", content).Result;

                            if (!response.IsSuccessStatusCode)
                            {
                                this.Invoke((MethodInvoker)delegate
                                {
                                    errorLabel.Text = $"Failed to start poll: {response.ReasonPhrase}";
                                });
                            }
                        }
                    });

                    MessageBox.Show("Poll request sent successfully.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception ex)
                {
                    errorLabel.Text = $"Failed to communicate with the server: {ex.Message}";
                }
            };
            this.Controls.Add(confirmButton);
        }

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}