# Bazaar blocklist policy

To help avoid unnecessary effort spent on deciding what belongs in here, this file defines our criteria for adding an app to the Bazaar blocklist. Of course, not every app on the list will be for the reasons below, and there will be exceptions to these rules. But if you're considering adding an app to the list, you should understand this criteria.

## Apps in scope

The primary goal of the blocklist is to block **web browsers**. For clarity, this means an application which has the *primary purpose* of fetching arbitrary data from arbitrary sources, potentially including automatic execution of **untrusted JavaScript code**.

This is because the majority of web browsers have *much weaker sandboxing* as flatpaks. There are partial mitigations to this problem, but nothing is able to completely resolve it. As such, we want to discourage installing browsers through Flatpak, and encourage much safer native installations.

As an exception, if a browser's internal sandboxing is designed to work within Flatpak, and it's not a significant security degradation relative to other methods, the browser can be permitted. The only known example of this is `org.gnome.Epiphany`.

## Apps not in scope

We do *not* want to exclude every app based on web technologies. Most of these are **web-based apps**, executing code which should be trusted by the developer. This makes the weakened sandbox less concerning, especially if you keep the Flatpak permissions strict. That said, we still encourage using PWA alternatives in Trivalent whenever possible, as they benefit from Trivalent's hardening and confinement.

We also don't want to start excluding apps which are *related* to browsers. For example, `dev.qwery.AddWater` installs a theme for Firefox. This app does *not* have a web engine, despite being directly tied to a program which does. While you can't acquire Firefox through Bazaar, it could be installed another way if the user truly desires. That is up to the user to decide.

## Examples

From unambiguously browsers, to unambiguously not browsers.

### `org.torproject.torbrowser-launcher`

Unambiguously a **web browser**. While it serves a unique purpose, it still belongs on the list, as it is much more secure to install using another method.

### `net.codelogistics.webapps`

Mostly unambiguous, but still a **web browser**. It isn't presented like a typical browser, instead acting more like a PWA installer. However, it still loads from arbitrary sources, rather than specific sources the developer has defined. Installing PWAs through Trivalent should be functionally identical and more secure.

### `org.mozilla.Thunderbird`

Ambiguous. Thunderbird is based on the same web engine as Firefox, and is capable of loading websites. However, Thunderbird's *primary purpose* is as an email client. And while emails are very adjacent to websites, as they *can* contain HTML, CSS, and images; they explicitly *cannot* contain JavaScript.

As such, Thunderbird is considered **not** a web browser, and instead fits our definition of a web-based app. It is *technically* capable of loading websites, but you must go out of your way to, and any method to do so is likely considered a bug.

### `com.valvesoftware.Steam`

Somewhat ambiguous, but **not** a web browser. The majority of the client fits into the category of web-based app, only loading from [steampowered.com](https://store.steampowered.com) or [steamcommunity.com](https://steamcommunity.com). There is an actual web browser which would definitely be unsafe, accessible through the in-game overlay or niche actions that open it; but this is a small part of the application, and the user can completely avoid it. As such, it is not the *primary purpose* of Steam.

### `app.fluxer.Fluxer`

Unambiguously **not** a web browser. It only loads one window containing [fluxer.app](https://fluxer.app), and any external links always open in the user's default browser, making it a web-based app.
