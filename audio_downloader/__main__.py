import importlib

main = importlib.import_module("audio_downloader.cli").main
raise SystemExit(main())
