# Rebocap × Linux × VRChat 全身追蹤實戰紀錄

在 Linux 上把 **Rebocap** 慣性動捕的全身追蹤接到 **VRChat**。不用 SteamVR，走 **WiVRn + xrizer**，頭顯是 Meta Quest。

這份紀錄包括實際環境、從零開始的安裝步驟、日常怎麼玩，以及途中遇到的每一個坑和解法。

```
Quest 頭顯 → WiVRn → rebocap-wivrn-bridge CLI → bridge.exe（Wine）→ Rebocap
Rebocap 追蹤器 → bridge.exe → CLI → SolarXR → WiVRn → xrizer → VRChat
```

## 實測環境

| 項目 | 版本／設定 |
|---|---|
| 系統 | Arch Linux（Omarchy，Hyprland），NVIDIA RTX 3070 |
| 頭顯 | Meta Quest，WiVRn（WiFi 或 USB） |
| WiVRn | wivrn-server / wivrn-dashboard 26.9 |
| xrizer | xrizer-git 0.6.r6（rebocap-wivrn-bridge 作者測試的是 0.5，0.6 也正常） |
| Rebocap | Windows 版，在 Flatpak **Bottles** 裡執行，runner 是 soda-11.0-10（有 ntsync） |
| 追蹤器 | 平常 10 點：腰、胸、雙腿、雙腳、雙上臂、雙前臂。測試時用 6 點：腰、雙大腿、雙小腿、胸 |

## 用到的專案

| 專案 | 用途 |
|---|---|
| [TW527E/rebocap-wine](https://github.com/TW527E/rebocap-wine) | setupapi 補丁，讓 Rebocap 在 Wine 裡認得接收器 |
| [TW527E/rebocap-linux-compat](https://github.com/TW527E/rebocap-linux-compat) | `bridge.exe`：在 Wine 裡把 Rebocap 的 named pipe 轉成 TCP。fork 自 [dogesoulseller/rebocap-linux-compat](https://github.com/dogesoulseller/rebocap-linux-compat)，加了 Bottles/ntsync 修正 |
| [akazdayo/rebocap-wivrn-bridge](https://github.com/akazdayo/rebocap-wivrn-bridge) | CLI（`monad2steamvr`）：在 WiVRn 和 bridge 之間轉送頭部與追蹤器姿勢，用 SolarXR 發布追蹤器 |
| 本 repo | 啟動腳本 `rebocap-fbt`、VRChat 按鍵綁定產生器、這份紀錄 |

## 安裝（從零開始）

### 1. 接收器權限

使用者要在擁有 `/dev/ttyACM*` 的群組裡（Arch 是 `uucp`），重開機後才會持續有效：

```sh
sudo usermod -aG uucp "$USER"   # 執行後要重新登入
```

我另外加了一條 udev 規則 `/etc/udev/rules.d/70-rebocap.rules`，可加可不加：

```
SUBSYSTEM=="tty", ATTRS{idVendor}=="248a", ATTRS{idProduct}=="8002", MODE="0660", TAG+="uaccess"
```

### 2. Rebocap 裝進 Bottles

1. Bottles 給予 `--device=all` 權限，Wine 才能存取序列埠。
2. 建立 Bottle（我取名 `Rebocap`，win64），安裝 Rebocap。
3. 套用 [rebocap-wine](https://github.com/TW527E/rebocap-wine) 的 setupapi 補丁，讓 Rebocap 能列舉到接收器。
4. 在 Bottle 的 `dosdevices` 把接收器對應成 COM 埠，例如 `com33 -> /dev/ttyACM0`。

### 3. bridge.exe

```sh
git clone https://github.com/TW527E/rebocap-linux-compat
cd rebocap-linux-compat
x86_64-w64-mingw32-gcc -O2 -static -o bridge.exe bridge/bridge.c -lws2_32   # 需要 mingw-w64-gcc
cp bridge.exe ~/.var/app/com.usebottles.bottles/data/bottles/bottles/Rebocap/drive_c/Program\ Files\ \(x86\)/Rebocap/
```

不想自己編譯的話，可以從 fork 的 Releases 下載 `bridge.exe`。

**不需要**執行它的 `install.py`，也不用註冊 SteamVR 驅動。

建議在 Bottles GUI 裡把 `bridge.exe` 加成這個 Bottle 的程式，方便日常啟動。

### 4. CLI

```sh
sudo pacman -S rust openxr pkgconf
git clone https://github.com/akazdayo/rebocap-wivrn-bridge ~/Downloads/rebocap-wivrn-bridge
cd ~/Downloads/rebocap-wivrn-bridge && cargo build --release
```

### 5. 啟動腳本

```sh
git clone https://github.com/TW527E/rebocap-linux-vrchat-fbt ~/Downloads/rebocap-linux-vrchat-fbt
ln -s ~/Downloads/rebocap-linux-vrchat-fbt/scripts/rebocap-fbt ~/.local/bin/rebocap-fbt
```

如果路徑不同，可以用環境變數覆寫：`REBOCAP_CLI`、`REBOCAP_BOTTLE`、`REBOCAP_RECEIVER`、`REBOCAP_XR_RUNTIME_JSON`。

### 6.（選用）右搖桿按下 = 跳躍

如果手把 A 鍵壞了，可以讓右搖桿按下也能跳。產生 xrizer 用的綁定檔：

```sh
./xrizer-bindings/make-vrchat-bindings.py      # 寫到 ~/.config/xrizer-bindings/oculustouch.json
```

然後在 VRChat 的 Steam 啟動選項最前面加上：

```
XRIZER_CUSTOM_BINDINGS_DIR=/home/<你>/.config/xrizer-bindings
```

右搖桿原本的功能是「Udon Stick Click」，只有少數世界會用到。A 鍵照樣可以跳。VRChat 更新後重跑一次產生器即可。要恢復原狀，刪掉這個啟動選項就好。

## 日常怎麼玩

**不玩全追**：照平常的方式就好，開 WiVRn → 頭顯連線 → 開 VRChat。不需要 Rebocap，也不需要腳本。

**全身追蹤**，**順序很重要**：

1. 開 **WiVRn**（wivrn-dashboard），確認伺服器在執行。**頭顯先不要連。**
2. 在 Bottles 開 **Rebocap**，再開 **bridge.exe**。
3. 終端機執行：
   ```sh
   rebocap-fbt          # 10 點（預設）
   rebocap-fbt 6        # 6 點
   rebocap-fbt 10 --usb # 準備好後自動用 USB 連頭顯
   ```
4. 看到「**SolarXR 準備好了**」（也會跳桌面通知）之後，**連頭顯**。
5. Rebocap 切到 **VR 模式**，戴著頭顯**校準**。
6. 從 Steam 開 **VRChat**，在快捷選單點 **Calibrate FBT**。

腳本會顯示部位檢查：

```
有資料的部位：0 1 2 5 6 7 9 10 11 12
  ⚠ 已發布但沒有資料：…
  ⚠ 有資料但沒有發布：…
```

出現 ⚠ 就代表部位參數和實際綁的追蹤器不一致，要修正部位參數。

**結束**：

1. 在腳本的終端機按 **Ctrl+C**。腳本會關掉 CLI，並用 `bridge.quit` 讓 bridge 自己退出。
2. 按 X 關掉 **Rebocap** 視窗。
3. WiVRn 照平常的方式處理。

**重要**：重啟 CLI 或換了部位之後，頭顯要**重新連線**，VRChat 也要**重開**。WiVRn 只在頭顯連線時讀取追蹤器清單。

### 部位編號

| 編號 | 部位 | 編號 | 部位 |
|---|---|---|---|
| 0 | 腰 | 7 | 胸 |
| 1 / 2 | 左／右大腿 | 9 / 10 | 左／右上臂 |
| 3 / 4 | 左／右小腿 | 11 / 12 | 左／右前臂 |
| 5 / 6 | 左／右腳 | | |

VRChat 校準時是依追蹤器的**位置**分配給臀、腳、膝、胸、肘，所以 6 點套組的小腿追蹤器可以當成腳來用。

CLI 預設的 `0,5,6` 只適合有綁腳的套組。6 點套組沒有腳的實體追蹤器，5、6 只是 Rebocap 建出的虛擬節點，只會送短暫的一點資料，用預設值的話 VRChat 會抓不到腳。

### USB 連線

1. 頭顯要開開發者模式，並允許這台電腦用 USB 偵錯。授權視窗會顯示在頭顯裡，要戴上才看得到。
2. 執行 `adb devices`，狀態應該是 `device`。如果是 `unauthorized`，代表頭顯還沒按允許。
3. 用 `rebocap-fbt --usb`，或在 wivrn-dashboard 按「透過 USB 連線」。

手動的話：

```sh
adb reverse tcp:9757 tcp:9757
adb shell am start -a android.intent.action.VIEW -d "wivrn+tcp://127.0.0.1:9757" org.meumeu.wivrn
```

## 踩過的坑

詳細的除錯過程在 [docs/troubleshooting.md](docs/troubleshooting.md)。重點如下：

| 症狀 | 原因 | 解法 |
|---|---|---|
| bridge.exe 顯示 listening，但連進去永遠沒有反應 | 這個 Wine（soda-11.0-10 + ntsync）的阻塞式 socket 呼叫是壞的 | bridge 改用非阻塞 socket 加事件等待（fork 已修） |
| 沒有腰的追蹤器、腳的資料斷斷續續、bridge 一直印 `0 bytes` | 讀 pipe 時回報 0 bytes，訊息被丟掉了 | 先用 `PeekNamedPipe` 確認有資料才讀（fork 已修） |
| bridge CPU 很高、Rebocap 完全不回應 | pipe 的讀取一直處於等待，IO 狀態永遠不會更新 | 同上 |
| 從終端機 `kill` bridge 後，Rebocap 當掉 | wineserver 在處理被殺的程序時 segfault | **永遠不要從主機 kill Wine 程序**，改用 `bridge.quit` |
| Rebocap 顯示「網路校驗失敗，10 秒後退出」然後卡住 | wineserver 已經不在了，Wine 裡的網路全部失效 | 結束整個 Bottle 再重開。不是網路本身的問題 |
| Bottles「停止」一直卡住 | bridge 是 console 程式，Rebocap 也不理會 Windows 的關機訊號 | 先 `bridge.quit`，再手動關 Rebocap 視窗 |
| CLI：`Failed to connect to monado service process` | WiVRn 伺服器沒在跑（dashboard 開著不代表伺服器開著） | 在 dashboard 按「啟動伺服器」 |
| CLI 找不到 WiVRn | 系統沒有 `active_runtime.json` | 加上 `XR_RUNTIME_JSON=/usr/share/openxr/1/openxr_wivrn.json`（腳本已自動加） |
| CLI 顯示 `invalid SolarXR frame` 加上用法說明 | 部位參數裡混了全形標點（例如 `12。`） | 只用半形數字和逗號 |
| VRChat 抓不到腳 | 部位參數和實際綁的追蹤器不一致 | 看腳本的部位檢查，修正部位參數 |

## 授權

本 repo 的腳本和文件採用 MIT License。`bridge.exe` 的程式碼來自 dogesoulseller/rebocap-linux-compat（MIT）。CLI 由 akazdayo/rebocap-wivrn-bridge 開發，本 repo 只放連結，不包含它的程式碼。Rebocap 是 JXQ 的專有軟體，本 repo 不包含它的任何檔案。
