# 除錯紀錄

這是實際接通的過程中，每個問題的症狀、我是怎麼確認原因的，以及最後的解法。

環境是 Rebocap 跑在 Flatpak Bottles 裡（runner soda-11.0-10，系統有 `/dev/ntsync`），WiVRn 26.9，xrizer 0.6。

## 1. bridge.exe 永遠不接受連線

**症狀**：bridge 印出 `listening on 127.0.0.1:36850`，`ss` 也看得到這個埠在監聽。但從主機連進去之後，一直沒有出現 `driver connected`，連線卡在 `CLOSE-WAIT`。

**確認**：
- bridge.exe 只有一個執行緒，停在 `ntsync_schedule`，表示它一直卡在 `accept()`。
- 寫了一個小測試程式，在**同一個 Bottle** 裡用另一個埠測不同的寫法：

| 寫法 | 結果 |
|---|---|
| 阻塞式 `accept()` | 失敗，錯誤碼 317 |
| `select()` 後再 `accept()` | `select` 回傳 -1 |
| 非阻塞 `accept()` 輪詢 | ✅ |
| `WSAEventSelect` + `WaitForSingleObject` | ✅ |
| 阻塞式 `recv()` | 回傳 -1，錯誤碼 997（`WSA_IO_PENDING`） |
| 事件等待後 `recv()` | ✅ |

**原因**：這個 Wine build 的阻塞式 socket 呼叫是壞的。

**解法**：socket 改成非阻塞，所有等待都透過 `WSAEventSelect` 事件；`send` 遇到 `WSAEWOULDBLOCK` 就重試。

## 2. 訊息遺失：沒有腰、腳的資料斷斷續續

**症狀**：bridge 大約每秒印 60 次 `dropping malformed pipe message: 0 bytes, header says 0`。CLI 收到的腰（tracker id 3）沒有 role，因為它的 `TrackerAdded` 沒收到，所以 CLI 不會發布它。

**原因**：overlapped `ReadFile` 的事件觸發時，Wine 還沒把 IO 狀態寫回。`GetOverlappedResult` 看到狀態還是 `STATUS_PENDING`，就直接當作成功，回報 0 bytes，那則訊息就被丟掉了。

**第一版修正**：事件觸發後，等 `OVERLAPPED.Internal` 不再是 `STATUS_PENDING` 才讀結果。遺失的問題解決了，腰也出現了。

## 3. 第一版修正的副作用：執行緒空轉，Rebocap 完全沒有回應

**症狀**：bridge 的讀取執行緒 CPU 57%，CLI 一直等不到 `Received a Rebocap protocol message`。

**原因**：Rebocap 暫時沒有資料可送時，讀取會一直處於等待中，而這個環境下 IO 狀態永遠不會更新。第一版測試時看起來正常，只是因為那時 Rebocap 一直有資料，每次讀取都立刻完成。

**最終解法**：先用 `PeekNamedPipe` 確認 pipe 裡有資料，才去讀。這樣讀取一定會立刻完成，完全不會進入那個壞掉的等待路徑。沒有資料時就 `Sleep(1)`。

## 4. 從主機 kill bridge 讓 Rebocap 當掉

**症狀**：用 `kill` 結束舊的 bridge.exe 後，Rebocap 跟著消失了。

**確認**：`coredumpctl` 裡有一筆 wineserver 的 SIGSEGV，時間點和 kill 一致：

```
remove_process_thread ← kill_thread ← terminate_process ← main_loop_epoll
```

**解法**：
- bridge 加了一個 `bridge.quit` 檔案：建立這個檔案後，bridge 會自己呼叫 `ExitProcess` 正常退出。
- 原則：**wineserver 還活著的時候，不要從主機 kill 任何 Wine 程序。**

## 5. 「網路校驗失敗，即將在 10 秒後退出」

**症狀**：Rebocap 連不上自己的授權伺服器，錯誤碼是亂碼（`Windows Error 0x6a7cbf70`）。

**確認**：當時 wineserver 已經不在了，Wine 程序變成沒有伺服器的孤兒。主機自己連那台伺服器是正常的（`47.86.58.16` 回 200）。

**解法**：
1. 先結束 wineserver。
2. 再清掉那些失去伺服器的 Wine 程序。這時已經沒有 wineserver，不會有崩潰風險。
3. 重開 Bottle。

## 6. 關閉時卡住

- `bottles-cli stop` 的關機流程是送出 Windows 的 end-session，然後執行 `wineserver -w` 等待。bridge 是 console 程式，Rebocap 也不理會這個訊號，所以會一直等下去。
- 從主機另外執行 `wineserver -k` 回傳 1，找不到伺服器。因為 wineserver 的 socket 在 Flatpak 沙盒自己的 `/tmp` 裡，主機的 `/tmp/.wine-1000/` 只看得到 `lock`。
- 結論：用 `bridge.quit` 關 bridge，Rebocap 手動關視窗。

## 7. 6 點套組用 CLI 預設值，VRChat 沒有腳

**確認**：統計各部位收到的姿勢筆數。

| 部位 | 筆數 |
|---|---|
| 0、1、2、3、4、7 | 持續送出（數千筆） |
| 5、6、9、10 | 每個只有 29 筆就停了，電量固定 1.0 |

Rebocap 校準 log 裡的 `failed node is:[0, 1, 2, 3, 4, 7]` 列出的也剛好是這 6 個。

**原因**：5、6、9、10 是 Rebocap 建出來的虛擬節點，不是實體追蹤器，不會持續送資料。

**解法**：部位參數照實際綁的追蹤器設定。6 點套組用 `0,1,2,3,4,7`。

## 8. 其他

- 系統沒有 `~/.config/openxr/1/active_runtime.json`，所以 CLI 要用 `XR_RUNTIME_JSON` 指定 WiVRn。
- WiVRn 伺服器可能隨著它啟動的應用程式結束而停止。這時 dashboard 還開著，但 `$XDG_RUNTIME_DIR/wivrn/comp_ipc` 已經不存在了。
- Quest 的 USB 偵錯授權視窗只會顯示在頭顯裡。頭顯休眠時，`lsusb` 也可能看不到它。
- xrizer 的自訂綁定檔名是 `<controller_type>` 去掉底線、轉成小寫，例如 Quest 手把是 `oculustouch.json`。它會在 `XRIZER_CUSTOM_BINDINGS_DIR` 裡找；沒有設定這個變數的話，會去遊戲工作目錄下的 `xrizer/` 找。
