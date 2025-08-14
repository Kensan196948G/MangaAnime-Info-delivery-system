  #!/usr/bin/env python3
  print('🧪 基本システムテスト')

  try:
      from modules.config import get_config
      config = get_config()
      print('✅ 設定読み込み成功')

      rss_config = config.get_rss_config()
      feeds = config.get_enabled_rss_feeds()
      print(f'RSS設定: {len(rss_config)} 項目')
      print(f'有効フィード: {len(feeds)} 件')

      from modules.db import DatabaseManager
      db = DatabaseManager('./db.sqlite3')
      print('✅ データベース接続成功')

      stats = db.get_work_stats()
      print(f'DB統計: {stats}')

      print('🎉 基本システム動作確認完了')

  except Exception as e:
      print(f'❌ エラー: {e}')
      import traceback
      traceback.print_exc()
