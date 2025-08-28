# Kijya

究極簡單的伺服器更新管理程式，利用 ZIP壓縮檔 升級伺服器程式。~~反正程式能動就好~~

https://github.com/fuseita/kijya

把這個檔案放到GitHub的專案裡面，就能讓程式神奇的自己更新自己本身。~~雖然走走還是看不懂這個程式怎麼動的~~

```yaml
name: 自動化更新系統 🖧

on:
  push:
    branches:
      - main

jobs:
  run-kijya:
    runs-on: ubuntu-latest
    steps:
      - name: 從 Git 下載資料 🛎️
        uses: actions/checkout@v4
          
      - name: 刪掉沒用到的資料 🔥
        run: rm -rf ${{ vars.KIJYA_REMOVE }}

      - name: 壓縮 Zip 📥
        uses: montudor/action-zip@v1
        with:
          args: zip -qq -r build.zip .

      - name: 上傳 Zip 🚀
        uses: JantHsueh/upload-file-action@master
        with:
          url: ${{ vars.KIJYA_URL }}
          forms: '{"password":"${{ secrets.KIJYA_PASS }}","path":"${{ vars.KIJYA_PATH }}","cmd":"${{ vars.KIJYA_CMD }}"}'
          fileForms: '{"file":"build.zip"}'
```

走走習慣使用[supervisord](http://supervisord.org)架設伺服器，這個設定檔你可以拿去用。~~反正他不知道我從伺服器偷出來給你用~~

```ini
[program:kijya]
command=/server/kijya/venv/bin/fastapi run --port 8100
directory=/server/kijya
user=server
startsecs=0
stopwaitsecs=0
autostart=true
autorestart=true
stdout_logfile=/server/kijya/stdout.log
stderr_logfile=/server/kijya/stderr.log
```

我們有個魔法可以生成一個 `.pex` 檔案，可以讓你把 Kijya 帶來帶去。~~反正就是四處亂跑~~

```bash
pip install -U pex
pex -r requirements.txt -D . -m app -o kijya.pex
```
