from app.models import UserRoleEnum

__all__ = ("ROLES_PERMISSIONS")


ROLES_PERMISSIONS = {
    UserRoleEnum.USER: {
        "user.profile.view",            # Просмотр своего профиля
        "user.profile.edit",            # Редактирование своего профиля (имя, статус и т.д.)
        "user.profile.upload_avatar",   # Загрузка своего аватара
        "user.profile.search_users",    # Поиск других пользователей
        "user.profile.view_any",        # Просмотр профилей других пользователей (базовый, без чувствительных данных)
        "user.contacts.manage",         # Управление своим списком контактов (добавление/удаление)
    }
}


PERMISSIONS = {
    # Профиль пользователя
    "user.profile.view",            # Просмотр своего профиля
    "user.profile.edit",            # Редактирование своего профиля (имя, статус и т.д.)
    "user.profile.upload_avatar",   # Загрузка своего аватара
    "user.profile.search_users",    # Поиск других пользователей
    "user.profile.view_any",        # Просмотр профилей других пользователей (базовый, без чувствительных данных)
    "user.contacts.manage",         # Управление своим списком контактов (добавление/удаление)

    # Чаты (личные и групповые/каналы, как участник)
    "chat.message.send",            # Отправка сообщений в чат (DM, группа, канал)
    "chat.message.view_history",    # Просмотр истории сообщений в чатах, в которых состоит
    "chat.dm.create",               # Создание личного чата (Direct Message)
    "chat.group.create",            # Создание группового чата
    "chat.channel.join",            # Присоединение к групповому чату
    "chat.group.leave",             # Выход из группы, в которой состоит
    "chat.channel.create"           # Создание канала
    "chat.channel.join",            # Присоединение к каналу
    "chat.channel.leave",           # Выход из канала, в котором состоит

    # Сообщения
    "message.edit_own",             # Редактирование своих сообщений
    "message.delete_own",           # Удаление своих сообщений
    "message.mark_as_read",         # Отметка сообщений как прочитанных
    "message.send_typing_indicator",# Отправка индикатора набора текста

    # Файлы
    "file.upload_own",              # Загрузка своих файлов в чаты
    "file.download_in_chat",        # Скачивание файлов из чатов, в которых состоит

    # CHAT_MODERATOR_PERMISSIONS (исходные "chat.manage_any_*" и "message.edit_any")
    "user.manage.block_any_in_chat", # Уточнено, что блокировка в рамках чата
    "chat.members.manage_any_in_group", # Оригинальное "chat.manage_any_group_members"
    "chat.members.manage_any_in_channel", # Оригинальное "chat.manage_any_channel_members"
    "chat.info.edit_any_group", # Оригинальное "chat.edit_any_group_info"
    "chat.info.edit_any_channel", # Оригинальное "chat.edit_any_channel_info"
    "message.edit_any_in_chat", # Оригинальное "message.edit_any" - уточнено, что в рамках чата
    "message.delete_any_in_chat", # Оригинальное "message.delete_any" - уточнено, что в рамках чата
    "file.delete_any_in_chat", # Оригинальное "file.delete_any" - уточнено, что в рамках чата
    "chat.members.assign_roles_in_group", # Оригинальное "chat.manage_any_group_roles" - уточнено до назначения ролей
    "chat.members.assign_roles_in_channel", # Оригинальное "chat.manage_any_channel_roles" - уточнено до назначения ролей

    # Управление пользователями
    "user.manage.block_any",                  # Блокировка любого пользователя системы (независимо от чата)
    "user.manage.delete_any",                 # Удаление любого пользователя системы
    "user.manage.view_sensitive_profile_any", # Просмотр чувствительных данных профилей (например, email)

    # Управление чатами (глобально)
    "chat.create.channel_any_type", # Создание каналов любого типа (публичный/приватный)
    "chat.delete.any_group",        # Удаление любой группы в системе
    "chat.delete.any_channel",      # Удаление любого канала в системе

    # Управление ролями и доступом
    "auth.roles.assign_global",     # Назначение глобальных ролей (например, "администратор системы")

    # Управление системой
    "system.access.admin_panel",    # Доступ к административной панели
    "system.logs.view",             # Просмотр системных логов
    "system.metrics.monitor",       # Мониторинг системных метрик
    "system.config.edit",           # (Добавлено) Редактирование системных настроек
}
