using MQTTnet;
using MQTTnet.Client;
using MQTTnet.Client.Options;
using MQTTnet.Client.Receiving;
using MQTTnet.Server;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace HR_System
{
    public partial class MainFormBroker : Form
    {
        private IMqttServer mqttServer;

        private ConcurrentDictionary<string, HashSet<string>> clientSubscriptions = new ConcurrentDictionary<string, HashSet<string>>();

        private ConcurrentDictionary<string, DateTime> clientConnectTime = new ConcurrentDictionary<string, DateTime>();

        public MainFormBroker()
        {
            InitializeComponent();
            btnStopServer.Enabled = false;
            UpdateStatus(false); // 초기 상태 표시
            txt_IP.Text = GetPCIP("Wi-Fi");
        }
        public static string GetPCIP(string i_strName)
        {
            for (int i = 0; i < System.Net.NetworkInformation.NetworkInterface.GetAllNetworkInterfaces().Length; i++)
            {
                if (System.Net.NetworkInformation.NetworkInterface.GetAllNetworkInterfaces()[i].Name == i_strName)
                    return System.Net.NetworkInformation.NetworkInterface.GetAllNetworkInterfaces()[i].GetIPProperties().UnicastAddresses[1].Address.ToString();
            }
            return "0.0.0.0";
        }

        private async void btnStartServer_Click(object sender, EventArgs e)
        {
            btnStartServer.Enabled = false;
            btnStopServer.Enabled = false;

            AppendLog("MQTT 브로커 시작 중...");

            var options = new MqttServerOptionsBuilder()
                .WithDefaultEndpoint()
                .WithDefaultEndpointPort(1883)
                .WithConnectionBacklog(100)
                .WithConnectionValidator(context =>
                {
                    AppendLog($"[클라이언트 연결] ClientId: {context.ClientId}");
                    context.ReasonCode = MQTTnet.Protocol.MqttConnectReasonCode.Success;
                })
                .Build();

            var factory = new MqttFactory();
            mqttServer = factory.CreateMqttServer();

            mqttServer.UseApplicationMessageReceivedHandler(ae =>
            {
                string topic = ae.ApplicationMessage.Topic;
                string payload = Encoding.UTF8.GetString(ae.ApplicationMessage.Payload);
                AppendLog($"수신됨 - Topic: {topic}, Payload: {payload}");
            });

            mqttServer.UseClientConnectedHandler(ae =>
            {
                AppendLog($"연결됨: {ae.ClientId}");
                clientConnectTime[ae.ClientId] = DateTime.Now;
                clientSubscriptions.TryAdd(ae.ClientId, new HashSet<string>());
                UpdateClientList();
            });
            mqttServer.UseClientDisconnectedHandler(ae =>
            {
                if (listView_Client.InvokeRequired)
                {
                    listView_Client.Invoke(new Action(() =>
                    {
                        ListViewItem itemToRemove = null;  // 👈 Invoke 내부에서 선언
                        foreach (ListViewItem item in listView_Client.Items)
                        {
                            if (item.SubItems[0].Text.Trim() == ae.ClientId.Trim())
                            {
                                itemToRemove = item;
                                break;
                            }
                        }

                        if (itemToRemove != null)
                        {
                            listView_Client.Items.Remove(itemToRemove);
                            if (clientSubscriptions.ContainsKey(ae.ClientId.Trim()))
                            {
                                clientSubscriptions.TryRemove(ae.ClientId.Trim(), out _);
                            }
                            AppendLog($"연결 해제됨: {ae.ClientId}");
                        }
                        else
                        {
                            AppendLog($" 클라이언트 {ae.ClientId} 항목을 찾을 수 없습니다.");
                        }
                    }));
                }
                else
                {
                    ListViewItem itemToRemove = null;
                    foreach (ListViewItem item in listView_Client.Items)
                    {
                        if (item.SubItems[0].Text.Trim() == ae.ClientId.Trim())
                        {
                            itemToRemove = item;
                            break;
                        }
                    }

                    if (itemToRemove != null)
                    {
                        listView_Client.Items.Remove(itemToRemove);
                        AppendLog($" 연결 해제됨: {ae.ClientId}");
                    }
                    else
                    {
                        AppendLog($" 클라이언트 {ae.ClientId} 항목을 찾을 수 없습니다.");
                    }
                }

                //UpdateClientList();
            });

            try
            {
                await mqttServer.StartAsync(options);
                AppendLog(" MQTT 브로커가 시작되었습니다 (포트 1883)");
                btnStopServer.Enabled = true;
                UpdateStatus(true);
            }
            catch (Exception ex)
            {
                AppendLog(" 브로커 시작 실패: " + ex.Message);
                btnStartServer.Enabled = true;
                UpdateStatus(false);
            }
        }

        private async void btnStopServer_Click(object sender, EventArgs e)
        {
            if (mqttServer != null)
            {
                AppendLog("MQTT 브로커 종료 중...");
                await mqttServer.StopAsync();
                AppendLog("MQTT 브로커가 종료되었습니다.");
                mqttServer = null;
                clientSubscriptions.Clear();
                clientConnectTime.Clear();
                btnStartServer.Enabled = true;
                btnStopServer.Enabled = false;
                UpdateStatus(false);
            }
        }
        private void UpdateClientList()
        {
            if (this.InvokeRequired)
            {
                this.Invoke(new Action(UpdateClientList));
                return;
            }

            listView_Client.BeginUpdate();
            listView_Client.Items.Clear();

            foreach (var kv in clientSubscriptions)
            {
                string clientId = kv.Key;
                string topics = string.Join(", ", kv.Value);
                string connectedAt = clientConnectTime.TryGetValue(clientId, out var dt) ? dt.ToString("MM-dd HH:mm:ss") : "-";
                var item = new ListViewItem(new[] { clientId, connectedAt, topics });
                listView_Client.Items.Add(item);
            }
            listView_Client.EndUpdate();
        }

        private void UpdateStatus(bool isRunning)
        {
            if (lblStatus.InvokeRequired)
            {
                lblStatus.Invoke(new Action(() => UpdateStatus(isRunning)));
                return;
            }

            lblStatus.Text = isRunning ? "서버 실행 중" : "서버 중지됨";
            lblStatus.ForeColor = isRunning ? System.Drawing.Color.Green : System.Drawing.Color.Red;
        }

        private void AppendLog(string message)
        {
            if (lstLog.InvokeRequired)
            {
                lstLog.Invoke(new Action(() => lstLog.Items.Add(message)));
            }
            else
            {
                lstLog.Items.Add(message);
            }
        }

        private void btn_exit_Click(object sender, EventArgs e)
        {
            this.Close();
        }
    }
}
