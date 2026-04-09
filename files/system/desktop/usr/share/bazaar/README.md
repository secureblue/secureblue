# Bazaar blocklist policy

To help avoid unnecessary effort spent on deciding what belongs in here, this file defines our criteria for adding an app to the Bazaar blocklist. Of course, not every app on the list will be for the reasons below, and there will be exceptions to these rules. But if you're considering adding an app to the list, you should understand this criteria.

## Definitions

"**Arbitrary**" means something which ***could not*** *be anticipated* by the developer of an application.

"**Arranged**" means something which ***is*** *anticipated* by the developer of an application.

"**Process-level** sandboxing" means *each* process created by an application *is individually sandboxed*.

"**Application-level** sandboxing" means *all* processes created by an application *are in one sandbox*.

"**Web engine**" means code which parses an HTML document, CSS stylesheets to calculate and render a desired layout, and JavaScript code for dynamic behavior. For the sake of this document, the *combination of all three* is necessary to constitute a **web engine**.

"**Web browser**", or "browsers", means an application which has the primary purpose of fetching **arbitrary data** from an **arbitrary source**, and passing it to a **web engine** to be parsed, potentially including automatic execution of **arbitrary JavaScript code**.

"**Web framework**" means code which utilizes the core functionality of a **web browser** to allow creation of a new application.

"**Web-based app**" means an application based on a **web framework** which fetches **arranged data** from **arranged sources**, and is ***not*** *expected* to execute **arbitrary JavaScript code**.

### Example uses

The **web engine** Blink is used by the **web browser** Chromium. Chromium then became the basis for many other **web browsers**, such as Google Chrome and Trivalent; as well as **web frameworks** like Electron, which allow development of **web-based apps**.

The contents of an editable free-form text box are considered **arbitrary data**, as there is no way to predict what the user would enter in the box.

The data received from an API request is considered **arranged data**, as the application expects this data and knows exactly what that data should look like.

## Apps in scope

The primary goal of the blocklist is to block **web browsers**.

This is partially to promote the usage of Trivalent, since it is already well integrated with secureblue. Usage of any other browser is almost certainly a security degradation, on top of adding massive attack surface from having multiple web browsers installed.

However, the primary reason is that the majority of web browsers are *incompatible with Flatpak sandboxing*. Flatpak sandboxing is **application-level**, and is incapable of more granularity than that without manual intervention by the application itself.

Browsers implement their own **process-level** sandboxing models, which isolate each loaded page from the system *and* from each other. However, the Flatpak sandbox fundamentally [breaks the browser's own sandboxing](https://github.com/containers/bubblewrap#limitations), as it needs deeper integration with the OS than Flatpak allows. Without directly changing how the browser operates, it can only use the **application-level** Flatpak sandbox.

Using only **application-level** sandboxing for a browser is a *major* security degradation. While it would be ideal to do both, **process-level** sandboxing is much more important, as this protects websites from *each other* as well. Additionally, it can be much more restrictive, as opposed to an application-level sandbox, which must have holes for functionality like accessing files and devices. Individual processes do not need these holes.

Chromium-based flatpaks, both **web browsers** and **web-based apps** alike, utilize a workaround shim called [Zypak](https://github.com/refi64/zypak). This essentially tricks Chromium into using the Flatpak sandbox for process-level sandboxing rather than its own. However, this is not capable of implementing the same low-level security functionality as the official Chromium sandbox.

Zypak is also a much more obscure project, maintained by one person, with no formal security auditing, and far less eyes watching it. This lack of scrutiny means it is less understood and less tested, and could be significantly weaker, perhaps even having major vulnerabilities which nobody has noticed because nobody has looked. Meanwhile, the Chromium sandbox is maintained by an entire team, and watched by the countless projects which rely on it. And since Zypak is a workaround which Chromium has no idea is even happening, we're dealing with unintended behavior that the Chromium team isn't accounting for.

Firefox-based flatpaks simply throw up their hands in defeat and [disable much of the Firefox internal sandbox](https://bugzilla.mozilla.org/show_bug.cgi?id=1756236). Technically, the Firefox codebase has a warning about this, however, [they intentionally disable the warning](https://hg-edge.mozilla.org/releases/mozilla-beta/rev/509d4746f2d6) in the official Flatpak. On top of all this, the Firefox internal sandbox itself is known to be weaker than Chromium's sandbox. While the following article is fairly old, and the situation has slightly improved, primarily by [switching to Wayland](https://www.firefox.com/en-US/firefox/121.0/releasenotes#note-789921) and implementing a [properly sandboxed audio service](https://github.com/mozilla/cubeb); much of the information within is still correct, and [Chromium has only continued to pull ahead](https://www.chromium.org/Home/chromium-security/quarterly-updates/), so it is still worth reading for more information: https://madaidans-insecurities.github.io/firefox-chromium.html

## Apps out of scope

We do not want to exclude every app which utilizes a **web engine** or **web framework**. For starters, this would be a monumentally long list, which would be painful to maintain. There are also many **web-based apps** which users expect to be available.

**Web-based apps** are *not* loading **arbitrary code**, and are designed to load one page at a time from an **arranged source**. This reduces the necessity for process-level sandboxing, since the executed code should be trusted by the developer of the application, and there shouldn't be concern of loaded pages attacking each other. In fact, some Electron apps completely disable the internal sandbox.

While there are still security concerns with **web-based apps**, and we would encourage you to use PWA alternatives in Trivalent whenever possible, these are much less of a concern, especially if you keep the Flatpak permissions strict.

We also don't want to start excluding apps which are *related* to browsers. For example, `dev.qwery.AddWater` installs a theme for Firefox. This app does *not* have a **web engine** and does *not* access **arbitrary code** itself, despite being directly tied to a program which does. While you can't acquire Firefox through Bazaar, it could be installed another way if the user truly desires. That is up to the user to decide.

## Examples

From unambiguously browsers, to unambiguously not browsers.

### `com.google.Chrome`

Unambiguously a **web browser**. If anything, it's *the* web browser.

### `org.torproject.torbrowser-launcher`

Unambiguously a **web browser**. While it serves a unique purpose, it still belongs on the list, as it is much more secure to install using another method.

### `net.codelogistics.webapps`

Mostly unambiguous, but still a **web browser**. It isn't presented like a typical browser, instead acting more like a PWA installer. But it does still fit our definition of fetching **arbitrary data** from an **arbitrary website** and potentially executing **arbitrary code**.

### `org.mozilla.Thunderbird`

Ambiguous. Thunderbird is based on the same **web engine** as Firefox, and it does load **arbitrary data** from **arbitrary sources**. And Thunderbird *is* capable of loading **arbitrary websites**, if you really try to force it to.

However, Thunderbird's *primary purpose* is as an email client. And while emails are very adjacent to websites, as they *can* contain HTML, CSS, and images; they explicitly *cannot* contain JavaScript. Or at least, it would never be executed. Which means that generally speaking, Thunderbird should *not* execute **arbitrary code**.

Thunderbird is also careful with loading external sources embedded in an email, to prevent the sender tracking that you've opened it. Despite handling **arbitrary data** from **arbitrary sources**, it responsibly handles that data well, and places heavy limitations on them, fitting closer to our definition of **arranged data**. You could also argue the data actually comes from an **arranged source**, since the email server has to be configured by the user, and all emails go through it first, and it could process if they're risky.

As such, Thunderbird is considered **not** a web browser, and instead fits our definition of a **web-based app**. Even with it being technically possible to use as a web browser, you must go out of your way to, and any method to do so is likely considered a bug.

### `com.valvesoftware.Steam`

Somewhat ambiguous, but **not** a web browser. The majority of the client fits into the category of **web-based app**, only loading from [steampowered.com](https://store.steampowered.com) or [steamcommunity.com](https://steamcommunity.com), which are **arranged sources**. There is an actual **web browser** which would definitely be unsafe, accessible through the in-game overlay or niche actions that open it; but this is a small part of the application, and the user can completely avoid it. As such, it is not the *primary purpose* of Steam.

### `app.fluxer.Fluxer`

Unambiguously **not** a web browser. It only loads one window containing [fluxer.app](https://fluxer.app), an **arranged source**, and any external links always open in the user's default browser. It is a **web-based app**.

### `org.gnome.Robots`

Unambiguously **not** a web browser. This video game doesn't contain any web technology whatsoever, and doesn't even have internet permissions. The only risk here is being killed by robots.

## Edge cases

If a browser officially implements process-level sandboxing within Flatpak, as an intentional method they expect you to use, and it's not a significant security degradation relative to other methods; the browser can be permitted. The only known example of this is `org.gnome.Epiphany`.

In some cases, a **web framework** is used to construct a new **web browser**. In this case, it should simply be treated as a **web browser**.
