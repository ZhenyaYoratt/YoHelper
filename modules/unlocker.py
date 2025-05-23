import winreg

keys_to_unlock = [
    ("DisableTaskMgr", "Отключение диспетчера задач", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("DisableRegistryTools", "Отключение редактора реестра", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("DisableCMD", "Отключение командной строки", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoControlPanel", "Отключение панели управления", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoFolderOptions", "Отключение опций папок", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoRun", "Отключение команды 'Выполнить'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoViewContextMenu", "Отключение контекстного меню", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoTrayContextMenu", "Отключение контекстного меню системного трея", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoFind", "Отключение поиска", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoDesktop", "Отключение рабочего стола", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoClose", "Отключение кнопки 'Выключить'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoLogoff", "Отключение кнопки 'Выйти'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoSetFolders", "Отключение настройки папок", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoRecentDocsMenu", "Отключение меню 'Последние документы'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoRecentDocsHistory", "Отключение истории 'Последние документы'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuSubFolders", "Отключение подменю 'Пуск'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuMorePrograms", "Отключение 'Больше программ'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuMFUprogramsList", "Отключение списка 'Часто используемые программы'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuEjectPC", "Отключение кнопки 'Извлечь устройство'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuNetworkPlaces", "Отключение 'Сетевые места'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuPinnedList", "Отключение закрепленного списка 'Пуск'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuMyMusic", "Отключение 'Моя музыка'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuMyPictures", "Отключение 'Мои изображения'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuMyVideos", "Отключение 'Мои видео'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuMyComputer", "Отключение 'Мой компьютер'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuMyDocuments", "Отключение 'Мои документы'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuRun", "Отключение 'Выполнить'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuSearch", "Отключение 'Поиск'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuHelp", "Отключение 'Справка'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuFavorites", "Отключение 'Избранное'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenuControlPanel", "Отключение 'Панель управления'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoStartMenu", "Отключение 'Пуск'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoRecentDocs", "Отключение 'Последние документы'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoNetHood", "Отключение 'Сетевое окружение'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoEntireNetwork", "Отключение 'Сеть'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Network"),
    ("NoDrives", "Отключение дисков", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoComputersNearMe", "Отключение 'Компьютеры рядом со мной'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoChangeStartMenu", "Отключение изменения 'Пуск'", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("DisallowCpl", "Отключение категории панели управления", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"),
    ("NoDispCPL", "Отключение свойств дисплея", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoDispBackgroundPage", "Отключение фона рабочего стола", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoDispScrSavPage", "Отключение заставки", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoDispAppearancePage", "Отключение внешнего вида", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoDispSettingsPage", "Отключение настроек", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoSecCPL", "Отключение настроек безопасности", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoPwdPage", "Отключение настроек паролей", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoAdminPage", "Отключение настроек администратора", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoProfilePage", "Отключение настроек профиля", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoDevMgrPage", "Отключение менеджера устройств", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoConfigPage", "Отключение настроек конфигурации", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"),
    ("NoWindowsUpdate", "Отключение обновлений Windows", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\WindowsUpdate"),
    ("NoWindowsStore", "Отключение магазина Windows", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\WindowsStore"),
    ("NoEdgeBrowser", "Отключение браузера Edge", "Software\\Policies\\Microsoft\\Edge"),
    ("NoOneDrive", "Отключение OneDrive", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\OneDrive"),
    ("NoCortana", "Отключение Cortana", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Cortana"),
    ("NoTelemetry", "Отключение телеметрии", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection"),
    ("NoDefender", "Отключение Windows Defender", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\WindowsDefender"),
    ("NoFirewall", "Отключение брандмауэра Windows", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\WindowsFirewall"),
    ("NoSecurityCenter", "Отключение центра безопасности", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\SecurityCenter"),
    ("NoActionCenter", "Отключение центра уведомлений", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\ActionCenter"),
    ("NoTaskbar", "Отключение панели задач", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Taskbar"),
    ("NoLockScreen", "Отключение экрана блокировки", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\LockScreen"),
    ("NoScreenSaver", "Отключение заставки", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\ScreenSaver"),
    ("NoSleep", "Отключение режима сна", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Power"),
    ("NoHibernate", "Отключение гибернации", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Power"),
    ("NoFastStartup", "Отключение быстрого запуска", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Power"),
    ("NoBatterySaver", "Отключение режима экономии заряда", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\BatterySaver"),
    ("NoBluetooth", "Отключение Bluetooth", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Bluetooth"),
    ("NoWiFi", "Отключение Wi-Fi", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\WiFi"),
    ("NoEthernet", "Отключение Ethernet", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Ethernet"),
    ("NoVPN", "Отключение VPN", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\VPN"),
    ("NoProxy", "Отключение прокси", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Proxy"),
    ("NoNetworkDiscovery", "Отключение обнаружения сети", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\NetworkDiscovery"),
    ("NoFileSharing", "Отключение общего доступа к файлам", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\FileSharing"),
    ("NoPrinterSharing", "Отключение общего доступа к принтерам", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\PrinterSharing"),
    ("NoRemoteDesktop", "Отключение удаленного рабочего стола", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\RemoteDesktop"),
    ("NoRemoteAssistance", "Отключение удаленной помощи", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\RemoteAssistance"),
    ("NoRemoteManagement", "Отключение удаленного управления", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\RemoteManagement"),
    ("NoWindowsHello", "Отключение Windows Hello", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\WindowsHello"),
    ("NoBiometrics", "Отключение биометрии", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Biometrics"),
    ("NoSmartScreen", "Отключение SmartScreen", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\SmartScreen"),
    ("NoFamilySafety", "Отключение семейной безопасности", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\FamilySafety"),
    ("NoParentalControls", "Отключение родительского контроля", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\ParentalControls"),
    ("NoGameMode", "Отключение игрового режима", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\GameMode"),
    ("NoGameBar", "Отключение игровой панели", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\GameBar"),
    ("NoGameDVR", "Отключение записи игр", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\GameDVR"),
    ("NoXboxServices", "Отключение служб Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxServices"),
    ("NoXboxGamePass", "Отключение Xbox Game Pass", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGamePass"),
    ("NoXboxLive", "Отключение Xbox Live", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxLive"),
    ("NoXboxNetworking", "Отключение сетевых функций Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxNetworking"),
    ("NoXboxAchievements", "Отключение достижений Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxAchievements"),
    ("NoXboxClips", "Отключение клипов Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxClips"),
    ("NoXboxFriends", "Отключение друзей Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxFriends"),
    ("NoXboxMessages", "Отключение сообщений Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxMessages"),
    ("NoXboxParties", "Отключение групп Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxParties"),
    ("NoXboxStore", "Отключение магазина Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxStore"),
    ("NoXboxSubscriptions", "Отключение подписок Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxSubscriptions"),
    ("NoXboxSettings", "Отключение настроек Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxSettings"),
    ("NoXboxSupport", "Отключение поддержки Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxSupport"),
    ("NoXboxUpdates", "Отключение обновлений Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxUpdates"),
    ("NoXboxBeta", "Отключение бета-версий Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxBeta"),
    ("NoXboxInsider", "Отключение Xbox Insider", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxInsider"),
    ("NoXboxFeedback", "Отключение отзывов Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxFeedback"),
    ("NoXboxPrivacy", "Отключение конфиденциальности Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxPrivacy"),
    ("NoXboxSafety", "Отключение безопасности Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxSafety"),
    ("NoXboxAccessibility", "Отключение доступности Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxAccessibility"),
    ("NoXboxFamily", "Отключение семейных настроек Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxFamily"),
    ("NoXboxParentalControls", "Отключение родительского контроля Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxParentalControls"),
    ("NoXboxGameStreaming", "Отключение потоковой передачи игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameStreaming"),
    ("NoXboxCloudGaming", "Отключение облачных игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxCloudGaming"),
    ("NoXboxRemotePlay", "Отключение удаленной игры Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxRemotePlay"),
    ("NoXboxConsoleStreaming", "Отключение потоковой передачи консоли Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxConsoleStreaming"),
    ("NoXboxGamePassUltimate", "Отключение Xbox Game Pass Ultimate", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGamePassUltimate"),
    ("NoXboxLiveGold", "Отключение Xbox Live Gold", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxLiveGold"),
    ("NoXboxGamePreviews", "Отключение предварительных версий игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGamePreviews"),
    ("NoXboxGameTrials", "Отключение пробных версий игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameTrials"),
    ("NoXboxGameDemos", "Отключение демо-версий игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameDemos"),
    ("NoXboxGameAddOns", "Отключение дополнений к играм Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameAddOns"),
    ("NoXboxGameUpdates", "Отключение обновлений игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameUpdates"),
    ("NoXboxGameMods", "Отключение модов для игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameMods"),
    ("NoXboxGameCheats", "Отключение читов для игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameCheats"),
    ("NoXboxGameGuides", "Отключение руководств по играм Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameGuides"),
    ("NoXboxGameTips", "Отключение советов по играм Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameTips"),
    ("NoXboxGameNews", "Отключение новостей об играх Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameNews"),
    ("NoXboxGameReviews", "Отключение обзоров игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameReviews"),
    ("NoXboxGameRatings", "Отключение рейтингов игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameRatings"),
    ("NoXboxGameAchievements", "Отключение достижений игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameAchievements"),
    ("NoXboxGameClips", "Отключение клипов игр Xbox", "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\XboxGameClips"),
]

def run_scan():
    results = []
    for key, description, path in keys_to_unlock:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ) as reg_key:
                winreg.QueryValueEx(reg_key, key)
                results.append((key, description, path))
        except FileNotFoundError:
            pass
        except PermissionError:
            print(f"Не удалось проверить ключ {key}. Недостаточно прав.")
    return results

def run_manual_unlock(keys_to_unlock):
    for key, description, path in keys_to_unlock:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_WRITE) as reg_key:
                winreg.DeleteValue(reg_key, key)
                print(f"Ключ {key} удалён.")
        except FileNotFoundError:
            print(f"Ключ {key} не найден.")
        except PermissionError:
            print(f"Не удалось удалить ключ {key}. Недостаточно прав.")