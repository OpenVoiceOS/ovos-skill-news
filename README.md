# <img src='./res/icon/news.png' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/> News Streams

News Streams catalog

## About 

News streams from around the globe

![](gui.png)
![](gui2.png)
![](gui3.png)

PRs adding new feeds welcome, especially for unsupported languages

Supported stations include:

- [EN / PT / ES / DE / RU / IT / FR] EuroNews (video + audio)
- [EN / DE / ES] Deutsche Welle (video + audio)
- [EN / EN-US / EN-GB / FR] Russia Today (video + audio)
- [EN-US] SkyStream (video + audio)
- [EN-US] TWC - The Weather Channel (video + audio)
- [EN-US] AP - Associated Press Hourly Radio News
- [EN-US] Fox News
- [EN-US] NPR News Now
- [EN-US] PBS NewsHour
- [EN-US] GPB - Georgia Public Broadcasting
- [EN-GB] BBC News
- [EN-CA] CBC News
- [EN-AU] ABC News Australia
- [ES-ES] RNE Radio Nacional de España
- [CA-ES] CCMA Catalunya Informació
- [PT-PT] TSF Rádio Notícias
- [PT-PT] Noticiários RDP África
- [NL] VRT Nieuws
- [DE] Ö3 Nachrichten
- [DE] DLF
- [DE] WDR
- [FI] YLE
- [SV] Ekot


### Installation

If you are using this skill, you have to [disable the official skill](https://mycroft-ai.gitbook.io/docs/skill-development/faq#how-do-i-disable-a-skill) because they are incompatible

To play https streams properly you also need to install vlc

```bash
sudo apt-get install vlc
```

and make it the default it in your .conf

```json
  "Audio": {
    "backends": {
      "local": {
        "active": false
      },
      "vlc": {
        "active": true
      }
    },
    "default-backend": "vlc"
  },
```

## Examples 

* "play the news"
* "play npr news"
* "play euronews"
* "play catalan news"
* "play portuguese news"
* "play news in spanish"

## Credits 
- JarbasAl

## Category
**Information**

## Tags
#news