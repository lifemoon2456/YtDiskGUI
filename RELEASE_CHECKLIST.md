# قائمة نشر إصدار GitHub

1. اختبر إنشاء فيديو ثم استرجاعه بملف صغير، وتحقق من رسالة التطابق.
2. نفّذ `pip install -r requirements-build.txt` ثم `.\build-windows.ps1`.
3. أنشئ ملف الإصدار الجاهز للأشخاص الآخرين:

   ```powershell
   .\package-release.ps1 -Version 0.1.0
   ```

   سينشئ `release\YTDISK-windows-x64-v0.1.0.zip` متضمنًا `YTDISK.exe` ومجلد `_internal` معًا.
4. أنشئ Tag وإصدارًا جديدًا في GitHub، وارفع ملف ZIP كـ Release asset.
5. لا ترفع `dist/` أو `build/` أو ملفات الفيديو الناتجة إلى المستودع؛ ملف `.gitignore` يستثنيها.
6. اذكر أن FFmpeg مطلوب، واربط [دليل البدء](docs/GETTING_STARTED_AR.md).
7. حافظ على النسبة والترخيص: هذا العمل يعتمد على [YtDisk الأصلي](https://github.com/ahmedfox1/YtDisk) من ahmedfox1 ومرخص بموجب MIT.
