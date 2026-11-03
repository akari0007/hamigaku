// ハミガキ判定プログラム（MakeCode の JavaScript 表示で使っている版：microbit-歯磨き (4).hex）
//
// 前提：歯ブラシは横向き（持ち手が水平）で使う。micro:bit の Y 軸が持ち手の方向。
// 送る番号：0 = 縦磨き, 1 = 横磨き, 2 = ぐるぐる磨き, 3 = 内側磨き
// ゲーム側（5つとも）はこの番号をそのまま受け取る。

let isConnected = false
let lastX = 0
let lastY = 0
let diffX = 0
let diffY = 0

// 起動時にBluetoothをオンにする
bluetooth.startUartService()

// BluetoothがMacBookと繋がった時の演出
bluetooth.onBluetoothConnected(function () {
    isConnected = true
    basic.showIcon(IconNames.Target)
    basic.pause(500)
    basic.showIcon(IconNames.Happy)
    basic.pause(1000)
    basic.clearScreen()
})

// 接続が切れた時
bluetooth.onBluetoothDisconnected(function () {
    isConnected = false
    basic.showIcon(IconNames.Sad)
})

// 正誤判定(O/X)を受信した時
bluetooth.onUartDataReceived(serial.delimiters(Delimiters.NewLine), function () {
    let received = bluetooth.uartReadUntil(serial.delimiters(Delimiters.NewLine))
    if (received == "O") {
        basic.showIcon(IconNames.Yes)
    } else if (received == "X") {
        basic.showIcon(IconNames.No)
    }
    basic.pause(1000)
    basic.clearScreen()
})

// メインループ
basic.forever(function () {
    if (!isConnected) {
        // 接続待機中のアニメーション
        basic.showIcon(IconNames.Diamond)
        basic.pause(250)
        basic.showIcon(IconNames.SmallDiamond)
        basic.pause(250)
    } else {
        // --- 動きと向き(Z軸)の検知 ---
        let currentX = input.acceleration(Dimension.X)
        let currentY = input.acceleration(Dimension.Y)
        let currentZ = input.acceleration(Dimension.Z)

        diffX = Math.abs(currentX - lastX)
        diffY = Math.abs(currentY - lastY)

        lastX = currentX
        lastY = currentY

        // 歯ブラシが動かされたか（しきい値400）
        if (diffX > 400 || diffY > 400) {

            // ★Z軸(画面の上下方向)に強い重力がかかっているか
            // 写真のようにブラシが上(または下)を向いている時に反応
            if (Math.abs(currentZ) > 700) {
                // ＝ 「歯の内側磨き (3)」
                bluetooth.uartWriteString("3\n")
                led.plot(4, 4)

            } else if (diffX > 400 && diffY > 400) {
                // 縦も横も同時に激しく動いている ＝ 「ぐるぐる磨き (2)」
                bluetooth.uartWriteString("2\n")
                led.plot(0, 0)

                // ▼ 縦・横の判定 ▼
                // 歯ブラシは横向きで使うので、ボードの X 軸が「歯の上下」、Y 軸が「持ち手の方向」になる
            } else if (diffX > diffY) {
                // X軸(歯の上下方向)の動きの方が大きい ＝ 「縦磨き (0)」
                bluetooth.uartWriteString("0\n")
                led.plot(2, 0)

            } else {
                // Y軸(持ち手の方向)の動きの方が大きい ＝ 「横磨き (1)」
                bluetooth.uartWriteString("1\n")
                led.plot(0, 2)
            }
            // ▲ 縦・横の判定ここまで ▲

            basic.pause(200)
            basic.clearScreen()
        }
    }
    basic.pause(100)
})