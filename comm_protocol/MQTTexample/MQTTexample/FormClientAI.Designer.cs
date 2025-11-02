namespace MQTTexample
{
    partial class FormClientAI
    {
        /// <summary>
        /// 필수 디자이너 변수입니다.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// 사용 중인 모든 리소스를 정리합니다.
        /// </summary>
        /// <param name="disposing">관리되는 리소스를 삭제해야 하면 true이고, 그렇지 않으면 false입니다.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form 디자이너에서 생성한 코드

        /// <summary>
        /// 디자이너 지원에 필요한 메서드입니다. 
        /// 이 메서드의 내용을 코드 편집기로 수정하지 마세요.
        /// </summary>
        private void InitializeComponent()
        {
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(FormClientAI));
            this.txtMessage = new System.Windows.Forms.TextBox();
            this.lstLog = new System.Windows.Forms.ListView();
            this.main = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.btn_send1 = new System.Windows.Forms.Button();
            this.txt_IP = new System.Windows.Forms.TextBox();
            this.btn_Connect = new System.Windows.Forms.Button();
            this.btn_send2 = new System.Windows.Forms.Button();
            this.btn_send3 = new System.Windows.Forms.Button();
            this.btn_Disconnect = new System.Windows.Forms.Button();
            this.button1 = new System.Windows.Forms.Button();
            this.SuspendLayout();
            // 
            // txtMessage
            // 
            this.txtMessage.Font = new System.Drawing.Font("맑은 고딕", 18F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.txtMessage.Location = new System.Drawing.Point(35, 288);
            this.txtMessage.Name = "txtMessage";
            this.txtMessage.Size = new System.Drawing.Size(194, 39);
            this.txtMessage.TabIndex = 0;
            this.txtMessage.Text = "내용";
            // 
            // lstLog
            // 
            this.lstLog.Columns.AddRange(new System.Windows.Forms.ColumnHeader[] {
            this.main});
            this.lstLog.Font = new System.Drawing.Font("맑은 고딕", 12F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.lstLog.FullRowSelect = true;
            this.lstLog.GridLines = true;
            this.lstLog.HideSelection = false;
            this.lstLog.Location = new System.Drawing.Point(235, 39);
            this.lstLog.Name = "lstLog";
            this.lstLog.Size = new System.Drawing.Size(1043, 384);
            this.lstLog.TabIndex = 1;
            this.lstLog.UseCompatibleStateImageBehavior = false;
            this.lstLog.View = System.Windows.Forms.View.Details;
            // 
            // main
            // 
            this.main.Text = "내용";
            this.main.Width = 1000;
            // 
            // btn_send1
            // 
            this.btn_send1.BackColor = System.Drawing.SystemColors.ActiveCaption;
            this.btn_send1.Font = new System.Drawing.Font("맑은 고딕", 14.25F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.btn_send1.Location = new System.Drawing.Point(35, 333);
            this.btn_send1.Name = "btn_send1";
            this.btn_send1.Size = new System.Drawing.Size(124, 77);
            this.btn_send1.TabIndex = 2;
            this.btn_send1.Text = "SEND TOPIC1";
            this.btn_send1.UseVisualStyleBackColor = false;
            this.btn_send1.Click += new System.EventHandler(this.btnSend_Click);
            // 
            // txt_IP
            // 
            this.txt_IP.Font = new System.Drawing.Font("맑은 고딕", 18F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.txt_IP.Location = new System.Drawing.Point(35, 39);
            this.txt_IP.Name = "txt_IP";
            this.txt_IP.Size = new System.Drawing.Size(194, 39);
            this.txt_IP.TabIndex = 3;
            this.txt_IP.Text = "192.168.0.100";
            // 
            // btn_Connect
            // 
            this.btn_Connect.BackColor = System.Drawing.Color.MediumAquamarine;
            this.btn_Connect.Font = new System.Drawing.Font("맑은 고딕", 14.25F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.btn_Connect.Location = new System.Drawing.Point(52, 84);
            this.btn_Connect.Name = "btn_Connect";
            this.btn_Connect.Size = new System.Drawing.Size(146, 77);
            this.btn_Connect.TabIndex = 4;
            this.btn_Connect.Text = "MQTT CONNECT";
            this.btn_Connect.UseVisualStyleBackColor = false;
            this.btn_Connect.Click += new System.EventHandler(this.btn_Connect_Click);
            // 
            // btn_send2
            // 
            this.btn_send2.BackColor = System.Drawing.SystemColors.ActiveCaption;
            this.btn_send2.Font = new System.Drawing.Font("맑은 고딕", 14.25F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.btn_send2.Location = new System.Drawing.Point(35, 416);
            this.btn_send2.Name = "btn_send2";
            this.btn_send2.Size = new System.Drawing.Size(124, 77);
            this.btn_send2.TabIndex = 5;
            this.btn_send2.Text = "SEND TOPIC2";
            this.btn_send2.UseVisualStyleBackColor = false;
            this.btn_send2.Click += new System.EventHandler(this.btnSend_Click);
            // 
            // btn_send3
            // 
            this.btn_send3.BackColor = System.Drawing.SystemColors.ActiveCaption;
            this.btn_send3.Font = new System.Drawing.Font("맑은 고딕", 14.25F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.btn_send3.Location = new System.Drawing.Point(35, 499);
            this.btn_send3.Name = "btn_send3";
            this.btn_send3.Size = new System.Drawing.Size(124, 77);
            this.btn_send3.TabIndex = 6;
            this.btn_send3.Text = "SEND TOPIC3";
            this.btn_send3.UseVisualStyleBackColor = false;
            this.btn_send3.Click += new System.EventHandler(this.btnSend_Click);
            // 
            // btn_Disconnect
            // 
            this.btn_Disconnect.BackColor = System.Drawing.Color.Salmon;
            this.btn_Disconnect.Font = new System.Drawing.Font("맑은 고딕", 14.25F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.btn_Disconnect.Location = new System.Drawing.Point(52, 181);
            this.btn_Disconnect.Name = "btn_Disconnect";
            this.btn_Disconnect.Size = new System.Drawing.Size(146, 82);
            this.btn_Disconnect.TabIndex = 7;
            this.btn_Disconnect.Text = "MQTT DISCONNECT";
            this.btn_Disconnect.UseVisualStyleBackColor = false;
            this.btn_Disconnect.Click += new System.EventHandler(this.btn_Disconnect_Click);
            // 
            // button1
            // 
            this.button1.BackColor = System.Drawing.Color.Red;
            this.button1.Font = new System.Drawing.Font("맑은 고딕", 14.25F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.button1.ForeColor = System.Drawing.SystemColors.ButtonHighlight;
            this.button1.Location = new System.Drawing.Point(1131, 499);
            this.button1.Name = "button1";
            this.button1.Size = new System.Drawing.Size(124, 77);
            this.button1.TabIndex = 8;
            this.button1.Text = "EXIT";
            this.button1.UseVisualStyleBackColor = false;
            this.button1.Click += new System.EventHandler(this.button1_Click);
            // 
            // FormClientAI
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1313, 623);
            this.Controls.Add(this.button1);
            this.Controls.Add(this.btn_Disconnect);
            this.Controls.Add(this.btn_send3);
            this.Controls.Add(this.btn_send2);
            this.Controls.Add(this.btn_Connect);
            this.Controls.Add(this.txt_IP);
            this.Controls.Add(this.btn_send1);
            this.Controls.Add(this.lstLog);
            this.Controls.Add(this.txtMessage);
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Name = "FormClientAI";
            this.Text = "Client";
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.TextBox txtMessage;
        private System.Windows.Forms.ListView lstLog;
        private System.Windows.Forms.ColumnHeader main;
        private System.Windows.Forms.Button btn_send1;
        private System.Windows.Forms.TextBox txt_IP;
        private System.Windows.Forms.Button btn_Connect;
        private System.Windows.Forms.Button btn_send2;
        private System.Windows.Forms.Button btn_send3;
        private System.Windows.Forms.Button btn_Disconnect;
        private System.Windows.Forms.Button button1;
    }
}

