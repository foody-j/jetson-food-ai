using MQTTnet;
using MQTTnet.Client;
using MQTTnet.Client.Options;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace MQTTexample
{
    public partial class FormClientAI : Form
    {
        private IMqttClient mqttClient;

        public string PubTopic1 = "AI/RBSensorInfo";
        public string PubTopic2 = "AI/RBProcessInfo";
        public string PubTopic3 = "AI/FryInfo";
        public string SUBTopic = "HR/Status";
        public FormClientAI()
        {
            InitializeComponent();
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
        private async Task InitializeMqtt()
        {
            var factory = new MqttFactory();
            mqttClient = factory.CreateMqttClient();

            var options = new MqttClientOptionsBuilder()
                .WithTcpServer(txt_IP.Text, 1883)
                .WithCleanSession()
                .WithProtocolVersion(MQTTnet.Formatter.MqttProtocolVersion.V311)
                .Build();

            mqttClient.UseConnectedHandler(async e =>
            {
                AppendLog("MQTT 브로커에 연결됨");

                await mqttClient.SubscribeAsync(new MqttTopicFilterBuilder()
                   .WithTopic(SUBTopic)
                   .Build());
                AppendLog($"구독 시작: {SUBTopic}");
            });

            mqttClient.UseDisconnectedHandler(e =>
            {
                AppendLog(" MQTT 연결 끊김");
            });

            // 수신 메시지 핸들러
            mqttClient.UseApplicationMessageReceivedHandler(e =>
            {
                string topic = e.ApplicationMessage.Topic;
                string payload = Encoding.UTF8.GetString(e.ApplicationMessage.Payload);

                AppendLog($"수신됨 - Topic: {topic}, 메시지: {payload}");
            });

            try
            {
                await mqttClient.ConnectAsync(options);
            }
            catch (Exception ex)
            {
                AppendLog("연결 실패: " + ex.Message);
            }
        }

        private async void btnSend_Click(object sender, EventArgs e)
        {
            Control pCtrl = sender as Control;
            int nNum = Convert.ToInt32(pCtrl.Name.Substring(pCtrl.Name.Length - 1));
            if (mqttClient == null || !mqttClient.IsConnected)
            {
                AppendLog("MQTT에 연결되어 있지 않습니다.");
                return;
            }

            string msg = txtMessage.Text.Trim();
            var message = new MqttApplicationMessage();
            if (string.IsNullOrEmpty(msg))
            {
                AppendLog("메시지를 입력하세요.");
                return;
            }
            JObject pObj = new JObject();
            //pObj.Add(msg);


            if (nNum == 1)
            {
                try
                {
                    pObj.Add("RBSensorInfo" , msg);
                    message = new MqttApplicationMessageBuilder()
                                    .WithTopic(PubTopic1)
                                    .WithPayload(Encoding.UTF8.GetBytes(pObj.ToString()))
                                    .WithExactlyOnceQoS()
                                    .WithRetainFlag(false)
                                    .Build();
                }
                catch (Exception ex)
                {
                    MessageBox.Show(ex.ToString());
                }

            }
            else if (nNum == 2)
            {
                pObj.Add("RBProcessInfo", msg );
                message = new MqttApplicationMessageBuilder()
                                .WithTopic(PubTopic2)
                                .WithPayload(Encoding.UTF8.GetBytes(pObj.ToString()))
                                .WithExactlyOnceQoS()
                                .WithRetainFlag(false)
                                .Build();
            }
            else
            {
                pObj.Add("FryInfo", msg );
                message = new MqttApplicationMessageBuilder()
                                .WithTopic(PubTopic3)
                                .WithPayload(Encoding.UTF8.GetBytes(pObj.ToString()))
                                .WithExactlyOnceQoS()
                                .WithRetainFlag(false)
                                .Build();
            }
            try
            {
                await mqttClient.PublishAsync(message);
                AppendLog("전송됨: " + msg);
            }
            catch (Exception ex)
            {
                AppendLog("전송 실패: " + ex.Message);
                return;
            }
        }

        private void AppendLog(string log)
        {
            if (lstLog.InvokeRequired)
            {
                lstLog.Invoke(new Action(() => lstLog.Items.Add(log)));
            }
            else
            {
                lstLog.Items.Add(log);
            }
        }

        private void btn_Connect_Click(object sender, EventArgs e)
        {
            InitializeMqtt().GetAwaiter();
        }

        private async void btn_Disconnect_Click(object sender, EventArgs e)
        {
            if (mqttClient != null)
            {
                await mqttClient.DisconnectAsync();
                mqttClient = null;
            }
        }

        private void button1_Click(object sender, EventArgs e)
        {
            this.Close();
        }
    }
}
