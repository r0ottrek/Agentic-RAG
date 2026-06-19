# From Cloud to Closet: Why I Moved My Website to Self-Hosted

There's a moment in every tech hobbyist's journey where you look at your cloud hosting bill, look at the hardware sitting around your house, and think:  "I could just run this myself."  That's exactly what I did. 
 Why Self-Host? 
 It wasn't just about saving money (though that's nice). Self-hosting my website gave me: 
 Full control  — No platform limitations, no vendor lock-in, no surprise policy changes 
 Real experience  — Managing a Linux server, systemd services, networking, and deployments is exactly what IT jobs require 
 A portfolio piece  — "I self-host my website on a Proxmox homelab" is a much better story than "I deployed to Vercel" 
 Learning by breaking  — I've learned more from troubleshooting my own infrastructure than any online course 
 The Migration Plan 
 Moving from cloud to self-hosted wasn't as scary as I expected. Here was my checklist: 
 Set up Proxmox VE  on the laptop (already done from previous homelab work) 
 Create an LXC container  — Debian 12, 2 CPU, 1GB RAM, 8GB disk 
 Install Node.js  and clone the Git repository 
 Set up Cloudflare Tunnel  to route roottrek.org to the container 
 Create systemd services  for auto-start and auto-restart 
 Update DNS  to point through the tunnel 
 Test everything  and cut over 
 The Production Setup 
 systemd service [Unit]
Description=Root Trek Website
After=network.target

[Service]
User=roottrek
WorkingDirectory=/home/roottrek/Website
ExecStart=/usr/bin/node /home/roottrek/Website/.next/standalone/server.js
Restart=always
RestartSec=5
EnvironmentFile=/home/roottrek/Website/.env
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/home/roottrek/Website

[Install]
WantedBy=multi-user.target The systemd service runs the Next.js app as a non-root user with security hardening.  NoNewPrivileges  prevents privilege escalation, and  ProtectSystem=strict  makes the filesystem read-only except for the app directory. 
 Deployment Workflow 
 I wrote a simple deployment script that runs on the server: 
 deploy.sh #!/bin/bash
cd /home/roottrek/Website
git pull origin main
npm ci --legacy-peer-deps
npm run build
sudo systemctl restart roottrek
echo "Deployed successfully!" The workflow is: write code locally → push to GitHub → SSH into the server → run  deploy.sh . The whole process takes about 2 minutes. 
 Problems I Hit 
 Nothing went perfectly on the first try. Here are the real issues I dealt with: 
 DNS propagation delays  — After switching DNS to the tunnel, it took a few hours for all DNS caches to update. During that time, some users hit the old host. 
 Prisma binary compatibility  — Prisma generates platform-specific binaries. Had to make sure the correct engine for Debian 12 (linux-arm64-openssl-3.0.x or similar) was included. 
 File permissions  — The app runs as user  roottrek  but git clone was done as root. Had to chown the entire directory. 
 Was It Worth It? 
 Absolutely. Self-hosting isn't for everyone — if you just want a blog, use WordPress or Ghost. But if you're building a career in IT, running your own infrastructure is the best hands-on experience you can get. Every DNS issue, every permission error, every systemd configuration is a real skill that transfers directly to the job. 
 The Real Value Self-hosting isn't about the money you save. It's about the skills you gain. When an interviewer asks "tell me about a time you troubleshot a production issue," you'll have real stories — not hypotheticals from a study guide. 
