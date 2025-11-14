# Microsoft Edge ブラウザキャッシュクリア手順

## 🔄 新しい機能を反映させるために必要です

チェックボックス機能など、新しいJavaScriptが正しく動作するためには、ブラウザのキャッシュをクリアする必要があります。

---

## 方法1: スーパーリロード（推奨・最速）

### キーボードショートカット
```
Ctrl + Shift + R
```

または

```
Ctrl + F5
```

**これだけで新しいJavaScriptが読み込まれます！**

---

## 方法2: キャッシュクリア（完全）

### 手順

1. **Microsoft Edgeを開く**

2. **設定メニューを開く**
   - `Ctrl + Shift + Delete` を押す
   - または、`...`（右上）→「設定」→「プライバシー、検索、サービス」

3. **「閲覧データをクリア」セクション**
   - 「クリアするデータの選択」をクリック

4. **以下を選択**
   - ✅ Cookie およびその他のサイト データ
   - ✅ キャッシュされた画像とファイル
   - ✅ ホストされているアプリ データ

5. **時間の範囲**
   - 「すべての期間」を選択

6. **「今すぐクリア」をクリック**

7. **ページを再読み込み**
   ```
   http://192.168.3.92:3030/calendar
   ```

---

## 方法3: シークレットモード（テスト用）

### 手順

1. **シークレットウィンドウを開く**
   ```
   Ctrl + Shift + N
   ```

2. **URLを入力**
   ```
   http://192.168.3.92:3030/calendar
   ```

**シークレットモードではキャッシュが使われません。**

---

## ✅ 確認方法

キャッシュクリア後、カレンダーページで：

1. **日付をクリック**

2. **モーダルに以下が表示されるか確認:**
   - ✅ チェックボックス（各リリース項目の左側）
   - ✅ 「全選択」「全解除」ボタン
   - ✅ 「選択した項目をGoogleカレンダーに登録」ボタン

3. **表示されていれば成功！**

---

## 🔍 JavaScriptが読み込まれているか確認

### ブラウザの開発者ツールで確認

1. **F12キーを押す**（開発者ツールを開く）

2. **「コンソール」タブをクリック**

3. **以下のメッセージを確認:**
   ```
   Calendar Enhanced UI: Initializing...
   Calendar Enhanced UI: Initialization complete
   Google Calendar Integration: Loaded
   ```

4. **エラーメッセージがないか確認**

5. **ネットワークタブで確認:**
   - `calendar-enhanced.js` - 200 OK
   - `calendar-google-integration.js` - 200 OK

---

## 🚨 トラブルシューティング

### 問題: チェックボックスが表示されない

**解決策:**
1. `Ctrl + Shift + R` でスーパーリロード
2. シークレットモードで確認
3. F12 → コンソールでエラー確認

### 問題: 古いモーダルが表示される

**解決策:**
1. ブラウザを完全に閉じる
2. Microsoft Edgeを再起動
3. URLにアクセス

### 問題: ボタンをクリックしても反応しない

**解決策:**
1. F12 → コンソールでJavaScriptエラー確認
2. `GoogleCalendarIntegration is not defined` エラーがある場合
   - スーパーリロード
   - JavaScriptファイルが読み込まれているか確認

---

## 📞 確認コマンド（開発者用）

ブラウザのコンソール（F12）で以下を実行:

```javascript
// GoogleCalendarIntegrationが定義されているか確認
typeof GoogleCalendarIntegration !== 'undefined'
// → true が返ればOK

// 関数が利用可能か確認
typeof GoogleCalendarIntegration.addAllReleases === 'function'
// → true が返ればOK

// リリースデータが読み込まれているか確認
typeof window.releasesData !== 'undefined'
// → true が返ればOK
```

---

**最も簡単な方法: Ctrl + Shift + R でスーパーリロード！**
