namespace HR_System
{
    partial class MainFormBroker
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
            this.lblStatus = new System.Windows.Forms.Label();
            this.btnStartServer = new System.Windows.Forms.Button();
            this.btnStopServer = new System.Windows.Forms.Button();
            this.lstLog = new System.Windows.Forms.ListView();
            this.Main = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.btn_exit = new System.Windows.Forms.Button();
            this.listView_Client = new System.Windows.Forms.ListView();
            this.SUB_ClientID = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.Date = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.txt_IP = new System.Windows.Forms.TextBox();
            this.SuspendLayout();
            // 
            // lblStatus
            // 
            this.lblStatus.BackColor = System.Drawing.SystemColors.ActiveCaption;
            this.lblStatus.Font = new System.Drawing.Font("맑은 고딕", 15.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.lblStatus.Location = new System.Drawing.Point(12, 34);
            this.lblStatus.Name = "lblStatus";
            this.lblStatus.Size = new System.Drawing.Size(243, 101);
            this.lblStatus.TabIndex = 13;
            this.lblStatus.Text = "label1";
            this.lblStatus.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            // 
            // btnStartServer
            // 
            this.btnStartServer.BackColor = System.Drawing.SystemColors.ActiveCaption;
            this.btnStartServer.Font = new System.Drawing.Font("맑은 고딕", 15.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.btnStartServer.Location = new System.Drawing.Point(56, 240);
            this.btnStartServer.Name = "btnStartServer";
            this.btnStartServer.Size = new System.Drawing.Size(124, 77);
            this.btnStartServer.TabIndex = 12;
            this.btnStartServer.Text = "BROKER START";
            this.btnStartServer.UseVisualStyleBackColor = false;
            this.btnStartServer.Click += new System.EventHandler(this.btnStartServer_Click);
            // 
            // btnStopServer
            // 
            this.btnStopServer.BackColor = System.Drawing.SystemColors.ActiveCaption;
            this.btnStopServer.Font = new System.Drawing.Font("맑은 고딕", 15.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.btnStopServer.Location = new System.Drawing.Point(56, 497);
            this.btnStopServer.Name = "btnStopServer";
            this.btnStopServer.Size = new System.Drawing.Size(124, 77);
            this.btnStopServer.TabIndex = 11;
            this.btnStopServer.Text = "BROKER STOP";
            this.btnStopServer.UseVisualStyleBackColor = false;
            this.btnStopServer.Click += new System.EventHandler(this.btnStopServer_Click);
            // 
            // lstLog
            // 
            this.lstLog.Columns.AddRange(new System.Windows.Forms.ColumnHeader[] {
            this.Main});
            this.lstLog.Font = new System.Drawing.Font("맑은 고딕", 11.25F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.lstLog.FullRowSelect = true;
            this.lstLog.GridLines = true;
            this.lstLog.HideSelection = false;
            this.lstLog.Location = new System.Drawing.Point(266, 34);
            this.lstLog.Name = "lstLog";
            this.lstLog.Size = new System.Drawing.Size(1315, 540);
            this.lstLog.TabIndex = 10;
            this.lstLog.UseCompatibleStateImageBehavior = false;
            this.lstLog.View = System.Windows.Forms.View.Details;
            // 
            // Main
            // 
            this.Main.Text = "내용";
            this.Main.Width = 1300;
            // 
            // btn_exit
            // 
            this.btn_exit.BackColor = System.Drawing.Color.IndianRed;
            this.btn_exit.Font = new System.Drawing.Font("맑은 고딕", 15.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.btn_exit.Location = new System.Drawing.Point(56, 725);
            this.btn_exit.Name = "btn_exit";
            this.btn_exit.Size = new System.Drawing.Size(124, 77);
            this.btn_exit.TabIndex = 14;
            this.btn_exit.Text = "EXIT";
            this.btn_exit.UseVisualStyleBackColor = false;
            this.btn_exit.Click += new System.EventHandler(this.btn_exit_Click);
            // 
            // listView_Client
            // 
            this.listView_Client.Columns.AddRange(new System.Windows.Forms.ColumnHeader[] {
            this.SUB_ClientID,
            this.Date});
            this.listView_Client.Font = new System.Drawing.Font("맑은 고딕", 18F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.listView_Client.FullRowSelect = true;
            this.listView_Client.GridLines = true;
            this.listView_Client.HideSelection = false;
            this.listView_Client.Location = new System.Drawing.Point(266, 580);
            this.listView_Client.Name = "listView_Client";
            this.listView_Client.Size = new System.Drawing.Size(1204, 406);
            this.listView_Client.TabIndex = 15;
            this.listView_Client.UseCompatibleStateImageBehavior = false;
            this.listView_Client.View = System.Windows.Forms.View.Details;
            // 
            // SUB_ClientID
            // 
            this.SUB_ClientID.Text = "SUB_ClientID";
            this.SUB_ClientID.Width = 500;
            // 
            // Date
            // 
            this.Date.Text = "Date";
            this.Date.Width = 500;
            // 
            // txt_IP
            // 
            this.txt_IP.Font = new System.Drawing.Font("맑은 고딕", 18F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(129)));
            this.txt_IP.Location = new System.Drawing.Point(56, 195);
            this.txt_IP.Name = "txt_IP";
            this.txt_IP.Size = new System.Drawing.Size(199, 39);
            this.txt_IP.TabIndex = 16;
            this.txt_IP.Text = "192.168.0.100";
            // 
            // MainFormBroker
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1920, 1080);
            this.Controls.Add(this.txt_IP);
            this.Controls.Add(this.listView_Client);
            this.Controls.Add(this.btn_exit);
            this.Controls.Add(this.lblStatus);
            this.Controls.Add(this.btnStartServer);
            this.Controls.Add(this.btnStopServer);
            this.Controls.Add(this.lstLog);
            this.Name = "MainFormBroker";
            this.Text = "Broker";
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Label lblStatus;
        private System.Windows.Forms.Button btnStartServer;
        private System.Windows.Forms.Button btnStopServer;
        private System.Windows.Forms.ListView lstLog;
        private System.Windows.Forms.Button btn_exit;
        private System.Windows.Forms.ListView listView_Client;
        private System.Windows.Forms.ColumnHeader SUB_ClientID;
        private System.Windows.Forms.ColumnHeader Date;
        private System.Windows.Forms.ColumnHeader Main;
        private System.Windows.Forms.TextBox txt_IP;
    }
}

