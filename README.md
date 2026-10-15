# Kodi Android APK Builder

> **Testing Notice**
> This repository is for code testing only.
> It is not actively maintained and may not receive continuous updates.
> If you find issues, please fork this repository and fix them in your fork.

> **Kodi 22 status**
> `Piers` follows Kodi's moving `master` branch and is not a final release yet. Builds can change or temporarily break when upstream changes. Select `Omega` for the current stable Kodi 21 branch.

### Build a custom Kodi APK entirely in your browser — no software to install

Everything happens on GitHub. You edit files here, click a button to build, and download the finished APK when it's ready.

---

## ⚡ Quick start (first time)

### Step 1 — Fork this repo
Click the **Fork** button at the top-right of this page. This creates your own copy where your builds will run.

### Step 2 — Enable Actions
In your fork, click the **Actions** tab → click **"I understand my workflows, go ahead and enable them"**.

### Step 3 — Build your first APK
1. Go to **Actions** → **🎬 Build Kodi APK** (left sidebar)
2. Click **Run workflow** (top-right of the workflow list)
3. Fill in the form that appears:

| Field | What to put |
|-------|-------------|
| Kodi version | `Piers` — rolling Kodi 22 prerelease (default) |
| Target device | `arm64-v8a` — works on most modern Android devices |
| App display name | Leave as `Kodi` or type your custom name (shown under the launcher icon) |
| Package ID | Leave as `org.xbmc.kodi` unless you want both official + custom installed |
| APK file name | Leave blank to auto-generate, or type a custom name e.g. `MyMedia-v1.0` |
| Pre-enable Unknown sources | `true` — lets users install third-party addons without digging into settings |
| Publish as Release | `true` — gives you a permanent download link |

4. Click the green **Run workflow** button
5. Wait ~90 minutes (first build only — later builds are ~20–30 min)
6. Go to the **Releases** section (right sidebar on your repo home page) to download the APK

---

## 🎨 Customizing your build

All customization is done by editing files in the `kodi-config/` folder directly in GitHub — no software needed.

### Change the app name, APK filename, or package ID
These are all set in the **Run workflow** form each time you build. No files to edit.

- **App display name** — what users see under the icon on their launcher (e.g. `MyMedia`)
- **APK file name** — what the downloaded file is called (e.g. type `MyMedia-v1.0` → saves as `MyMedia-v1.0.apk`). Leave blank to auto-generate as `{AppName}-{Branch}-{ABI}.apk`
- **Package ID** — Android's internal identifier. Change this (e.g. `com.myname.mymedia`) to install your build alongside the official Kodi app

### Custom launcher icon
1. Open `kodi-config/` folder in your repo
2. Click **Add file → Upload files**
3. Upload a PNG named exactly `icon.png` (1024×1024 recommended)
4. Commit, then trigger a new build

### Custom splash screen
Same as above but upload `splash.png` (1920×1080 recommended).

### Pre-install addons
1. Open `kodi-config/addons.txt`
2. Click the **pencil icon** to edit in browser
3. Add one addon ZIP URL per line (find URLs at mirrors.kodi.tv/addons/piers/)
4. Click **Commit changes**
5. Trigger a new build — addons are baked in automatically

### Pre-enable Unknown sources
Set the **Pre-enable Unknown sources** option to `true` in the Run workflow form. This pre-enables the **Settings → System → Add-ons → Unknown sources** toggle so users can install third-party addons without having to find and enable it themselves. It can still be toggled off by the user after install.

### Pre-configure settings
- Edit `kodi-config/advancedsettings.xml` for buffer size, playback settings, etc.
- Edit `kodi-config/sources.xml` to pre-add media sources AND File Manager URL sources (see below)
- Drop a custom `kodi-config/guisettings.xml` to fully override any Kodi GUI setting at first launch

### Add File Manager URL sources
The **System → File Manager** in Kodi lets you add named URL sources — addon repo URLs, SMB shares, FTP paths, etc. You can pre-populate these so they appear on first launch without the user having to type anything.

Edit `kodi-config/sources.xml` in GitHub and add entries to the `<files>` section at the bottom of the file. The file already contains ready-to-use commented examples for every common type:

| Type | Example path |
|------|-------------|
| HTTP addon repo | `https://example.com/kodi-repo/` |
| HTTPS addon repo | `https://mirrors.kodi.tv/addons/piers/` |
| SMB share (no auth) | `smb://192.168.1.100/shared/` |
| SMB share (with login) | `smb://user:pass@192.168.1.100/private/` |
| FTP server | `ftp://user:pass@ftp.example.com/path/` |
| NFS share | `nfs://192.168.1.100/mnt/data/` |

To add a source: open `kodi-config/sources.xml` → click the pencil ✏️ icon → find the relevant commented example → remove the `<!--` and `-->` comment markers → replace the name and path → commit → trigger a build.

---

## 📲 Installing the APK on your Android device

1. Go to **Releases** on your repo page → download the `.apk` file
2. On your Android device: **Settings → Security → Unknown sources → ON**
   *(on newer Android: Settings → Apps → Special app access → Install unknown apps)*
3. Open the downloaded APK file on the device
4. Tap **Install**

---

## ❓ FAQ

**How long does a build take?**
First build: ~90 min. Subsequent builds with the same Kodi version: ~20–30 min (depends cache is reused by GitHub).

**Is it free?**
Yes. GitHub gives free accounts **2,000 minutes/month** on Linux runners. Each build uses ~90 min, so roughly 20+ free builds per month.

**Why does the APK say "untrusted" when installing?**
It's signed with a self-generated debug key — this is normal for custom builds. Android will warn about unknown sources, which you already enabled. It's safe.

**Can I install this alongside the official Kodi from the Play Store?**
Yes — change the Package ID to something like `com.myname.mykodi` in the build form. Different package IDs = separate apps.

**Can I control what the APK file is named when I download it?**
Yes — type anything in the **APK file name** field in the Run workflow form (e.g. `MyMedia-v1.0`). It saves as `MyMedia-v1.0.apk`. Leave it blank and it auto-generates as `{AppName}-{Branch}-{ABI}.apk`.

**What does "Pre-enable Unknown sources" actually do?**
It pre-sets the **Settings → System → Add-ons → Unknown sources** toggle to ON inside the APK, so users don't have to find and enable it manually before installing third-party addons. Users can still turn it off after install if they want.

**How do I pre-add File Manager sources (repo URLs, network shares)?**
Edit `kodi-config/sources.xml` and add entries to the `<files>` section. The file has ready-made commented examples for HTTP repos, SMB, FTP, and NFS. Uncomment the ones you need, fill in the URL and name, commit, and rebuild.

**Can I build for older devices?**
Yes — choose `armeabi-v7a` in the build form for 32-bit older devices.

**How do I update to a newer Kodi version?**
Trigger a new build and select the release you want. `Piers` follows the current Kodi 22 `master` branch, so later runs automatically pick up upstream prerelease changes. Omega, Nexus, and Matrix remain available for older builds.

---

## 📁 Repo structure

```
kodi-cloud-builder/
├── .github/
│   └── workflows/
│       └── build-kodi.yml        ← The build pipeline (don't need to touch this)
├── kodi-config/
│   ├── addons.txt                ← Your addon URLs (edit me in browser)
│   ├── advancedsettings.xml      ← Kodi settings baked in (edit me in browser)
│   ├── sources.xml               ← Media sources baked in (edit me in browser)
│   ├── icon.png                  ← Upload your custom icon here
│   ├── splash.png                ← Upload your custom splash here
│   └── IMAGES.md                 ← Icon/splash upload instructions
└── README.md                     ← This file
```

---

## 🔁 Typical workflow after setup

```
1. Edit kodi-config/ files in GitHub browser  (1 min)
2. Actions → Build Kodi APK → Run workflow    (1 min)
3. Wait for build to finish                   (~25 min with cache)
4. Download APK from Releases                 (1 min)
```
