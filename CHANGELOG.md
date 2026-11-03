# Changelog

## 3.1.34
- Windows-Unterstützung für Quellcodebetrieb ergänzt: Konfiguration unter `%APPDATA%\\LunaTresor`.
- Plattformabhängige Verzeichnissuche und Dateirechtebehandlung ergänzt.
- Windows-Startanleitung und `requirements.txt` hinzugefügt; keine EXE und kein Installer.

## 3.1.33
- Bestätigungsdialoge verwenden lokalisierte Schaltflächen „Ja/Nein“ bzw. „Yes/No“, insbesondere beim Löschen von Einträgen.


## 3.1.32
- Sprachwechsel aktualisiert Menüs, Schaltflächen, Tabellenüberschriften und Beschriftungen sofort ohne Neustart.
- Ein geöffneter Tresor und die aktuelle Anwendungssitzung bleiben beim Neuaufbau der Oberfläche erhalten.


## 3.1.31
- Info-Dialog ergänzt um den Copyright-/Markenhinweis „Goldisoft 2026“.


## 3.1.30
- Info-Aktion mit ⓘ-Symbol wieder direkt in die Menüleiste aufgenommen.
- Info-Dialog zeigt Version, Qt/PySide6-Oberfläche und KDBX-Format; Texte folgen der gewählten Sprache.

## 3.1.29
- Fixed light-theme menu visibility with explicit menu-bar, menu-item, and dropdown text/background colors and hover states.

## 3.1.28
- Transferred 8 px (about 2 mm) from the Password column to the Username column: Username 118 px, Password 84 px.

## 3.1.27
- Corrected column sizing with explicit fixed widths and a 10 px minimum section size.
- Favorites column is 23 px (15 px / approx. 4 mm narrower than 38 px); the same 15 px is transferred to Username, which is fixed at 110 px while the other columns stretch evenly.

## 3.1.26
- Reduced the Favorites column from 23 px to 8 px (a further 4 mm narrower).
- Increased the Username column starting width from 120 px to 155 px.

## 3.1.25
- Reduced the Favorites column from 38 px to 23 px (about 4 mm narrower).
- Gave the Username column a wider starting width so usernames are easier to read.

## 3.1.24
- The Favorites column is fixed at 38 px (about 1 cm); the remaining eight columns share the available table width equally.

## 3.1.23
- All nine entry-table columns now use equal widths and automatically fill the available table width.

## 3.1.22
- The final Notes column now stretches to the right edge of the entries table, removing the unused blank area.

## 3.1.21
- Narrowed the main window by 38 px (approximately 1 cm at typical desktop scaling).
- Reduced table column widths so the Notes column fits in the visible table without horizontal scrolling at the default window size.
- Full cell contents are available as tooltips when text is longer than the column.

## 3.1.20
- Added the missing Notes column to the entries table.
- Group labels no longer include the artificial KDBX root group; root-level entries display as Allgemein/General.

## 3.1.19
- Removed the redundant top header 'Open vault' button; left-side open button and File menu remain.
- PIN entry dialogs now use LunaTresor's own localized buttons (Abbrechen/OK in German, Cancel/OK in English) rather than untranslated Qt standard buttons.

## 3.1.18
- Fixed PIN setup: import Scrypt and AESGCM from cryptography; 3.1.17 referenced AESGCM without importing it, so PIN creation failed with NameError.
- PIN key derivation now reports a clear missing-dependency error if cryptography is unavailable.

## 3.1.17
- PIN settings are written atomically and read back for verification.
- PIN setup now reports an explicit success or the exact save error instead of silently appearing to succeed.
- Existing configuration keys are preserved when saving.

## 3.1.16
- PIN-configured vaults now unlock with the PIN only; no master-password fallback prompt is shown.
- Master password is requested only when no PIN is configured.
- Incorrect PIN leaves the vault locked and does not modify vault or PIN data.

# Changelog

## 3.1.12
- Only the vault-name row now stretches to the available width inside the existing vault list.
- The main window, left panel, splitter proportions, and all other layout dimensions remain unchanged from 3.1.8.
- Full vault filename remains unchanged and is displayed without truncation whenever it fits the existing panel width.

## 3.1.13
- Added a visible live password-strength indicator directly below the password field in the new/edit entry dialog.
- Strength updates on every keystroke and immediately when editing an existing entry or generating a password.
- Added five quality levels, including "Very strong" / "Sehr stark".
