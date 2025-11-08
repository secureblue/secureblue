import "@typespec/json-schema";
using TypeSpec.JsonSchema;

@jsonSchema("/modules/brew-latest.json")
model BrewModuleLatest {
  ...BrewModuleV1;
}

@jsonSchema("/modules/brew-v1.json")
model BrewModuleV1 {
  /** The brew module installs Homebrew / Linuxbrew at build time and ensures the package manager remains up-to-date.
   * https://blue-build.org/reference/modules/brew/
   */
  type: "brew" | "brew@v1" | "brew@latest";

  /** Whether to auto-update the Brew binary using a systemd service. */
  `auto-update`?: boolean = true;

  /** Defines how often the Brew update service should run. The string is passed directly to `OnUnitInactiveSec` in systemd timer. (Syntax: ['1d', '6h', '10m']). */
  `update-interval`?: string = "6h";

  /** Time delay after system boot before the first Brew update runs. The string is passed directly to `OnBootSec` in systemd timer. (Syntax: ['1d', '6h', '10m']). */
  `update-wait-after-boot`?: string = "10min";

  /** Whether to auto-upgrade all installed Brew packages using a systemd service. */
  `auto-upgrade`?: boolean = true;

  /** Defines how often the Brew upgrade service should run. The string is passed directly to `OnUnitInactiveSec` in systemd timer. (Syntax: ['1d', '6h', '10m']). */
  `upgrade-interval`?: string = "8h";

  /** Time delay after system boot before the first Brew package upgrade runs. The string is passed directly to `OnBootSec` in systemd timer. (Syntax: ['1d', '6h', '10m']). */
  `upgrade-wait-after-boot`?: string = "30min";

  /** Whether to increase nofile limits (limits for number of open files) for Brew installations.
   * When set to true, it increases the nofile limits to prevent certain "I/O heavy" Brew packages from failing due to "too many open files" error.
   * However, it's important to note that increasing nofile limits can have potential security implications for malicious applications which would try to abuse storage I/O.
   * Defaults to false for security purposes.
   *
   * https://serverfault.com/questions/577437/what-is-the-impact-of-increasing-nofile-limits-in-etc-security-limits-conf
   */
  `nofile-limits`?: boolean = false;

  /** Whether to enable Brew analytics.
   * The Homebrew project uses analytics to anonymously collect the information about Brew usage & your system in order to improve the experience of Brew users.
   */
  `brew-analytics`?: boolean = true;

  /** Whether to skip ublue's cache and directly install from Homebrew using the official installer.
   * Ublue provides a tarball cache of a Homebrew installation.
   */
  `direct-pull`?: boolean = false;

  /** The commit to use when directly pulling the Homebrew install script.
   * Defaults to "HEAD".
   */
  `installer-commit`?: string = "HEAD";
}
