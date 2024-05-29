12 . PING SERVICE SERVER LOCAL

```
sudo nano /etc/systemd/system/ping.service

```

```
[Unit]
Description=Decoder Program
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/localping/localping.py
WorkingDirectory=/home/localping
Restart=always
User=root
Group=root
[Install]
WantedBy=multi-user.target
```






13. Recarregue o systemd:
```bash
sudo systemctl daemon-reload
```
14. Inicie e habilite os serviços:

```bash
sudo systemctl start ping
sudo systemctl enable ping
