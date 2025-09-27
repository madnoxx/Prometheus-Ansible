# Развертывание микросервиса с Prometheus метриками через Ansible

Этот проект развёртывает простой HTTP-микросервис, экспортирующий метрики для Prometheus на порт 8080. Развертывание осуществляется с помощью Ansible на виртуальную машину под управлением Rocky Linux.

**Ключевые особенности:**

*   Весь процесс настройки и развертывания автоматизирован и управляется Ansible Playbook и ролями.
*   **Два режима развертывания:**
    1.  **`vm` (по умолчанию):** микросервис запускается напрямую на ВМ как служба `systemd`.
    2.  **`container`:** микросервис запускается внутри Docker-контейнера на той же ВМ.
*   **Динамическое определение среды:** микросервис определяет, запущен ли он напрямую на ВМ, в контейнере или на физическом сервере, и отдает соответствующую метрику `host_info{type="..."}`.

## Предварительные требования

Перед запуском убедитесь, что у вас настроено следующее окружение:

1.  Установлен любой гипервизор 2-го типа (например, VirtualBox, VMware Workstation/Player).
2.  **Виртуальные машины:**
    *   **Целевая ВМ:**
        *   ОС: Rocky Linux.
        *   Установлен и настроен SSH-сервер:
            ```bash
            sudo systemctl status sshd (если нет, sudo systemctl start sshd && sudo systemctl enable sshd)
            ```
        *   Установлен Docker (согласно официальной инструкции https://docs.docker.com/engine/install/centos/).
        *   Создан пользователь для Ansible (например, `ansible`):
            ```bash
            sudo useradd -m ansible
            sudo passwd ansible
            sudo usermod -aG wheel ansible
            ```
        *   Пользователь Ansible  добавлен в группу `docker`:
            ```bash
            sudo usermod -aG docker ansible
            ```
    *   **Управляющая ВМ:**
        *   ОС: любая Linux-система, например, Debian, Kali, Ubuntu, CentOS.
        *   Установлен **Ansible**: `sudo apt update && sudo apt install ansible-core -y` (для Debian/Ubuntu).
        *   Установлен **Python 3**.
        *   Установлена коллекция Ansible для Docker: `ansible-galaxy collection install community.docker`.
4.  Управляющая ВМ должна иметь сетевой доступ к целевой ВМ по IP-адресу.
5.  Настроен **беспарольный** доступ по SSH-ключам с управляющей ВМ на целевую ВМ для пользователя Ansible:
    *   На Управляющей ВМ (если ключей нет): `ssh-keygen`
    *   Скопировать ключ: `ssh-copy-id <ВАШ_ПОЛЬЗОВАТЕЛЬ_НА_ROCKY>@<IP_АДРЕС_ROCKY>`
7.  Настройте **беспарольные** права `sudo` для пользователя Ansible с помощью `sudo visudo` на целевой ВМ, добавив строку: `ansible ALL=(ALL) NOPASSWD: ALL`.

## Настройка перед запуском
1.  Распакуйте архив на вашей **управляющей ВМ** (например, Debian):
    *   Для `.zip`:
        ```bash
        unzip КОРОТАЕВ_ДМИТРИЙ_DEVOPS.zip -d devops-task
        cd devops-task
        ```
2.  **Настройте inventory:**
    *   Откройте файл `ansible/inventory`.
    *   Замените IP-адрес на реальный адрес вашей целевой ВМ.
    *   Вставьте имя пользователя, созданного для Ansible на целевой ВМ (например, `ansible`).
3.  **Проверьте SSH и sudo:**
    *   С управляющей ВМ выполните: `ssh <ВАШ_ПОЛЬЗОВАТЕЛЬ_НА_ROCKY>@<IP_АДРЕС_ROCKY> 'echo SSH OK'` (не должно запрашивать пароль).
    *   Зайдите на целевую ВМ и проверьте sudo: `sudo -l -U <ВАШ_ПОЛЬЗОВАТЕЛЬ_НА_ROCKY>` (должно показать, что команды можно выполнять без пароля).

## Запуск развертывания

Все команды выполняются с **управляющей ВМ** из корневой папки проекта.

**1. Развертывание на ВМ (режим `vm`):**

```bash
ansible-playbook -i ansible/inventory ansible/playbook.yml -e deploy_method=vm
```
**2. Развертывание в контейнере (режим `container`):**
```bash
ansible-playbook -i ansible/inventory ansible/playbook.yml -e deploy_method=container
```

## Проверка результата

После успешного выполнения плейбука проверьте результат на **целевой ВМ (Rocky Linux)**.

### Для режима `vm`

1.  **Статус службы systemd:**
    ```bash
    sudo systemctl status my_microservice
    ```
    *   Ожидаемый вывод: `Active: active (running)`

2.  **Отсутствие контейнера:**
    ```bash
    sudo docker ps
    ```
    *   Ожидаемый вывод: Контейнер `my_microservice` *не должен* быть в списке запущенных.

3.  **Метрики:** Откройте в браузере или через `curl`:
    ```bash
    # На самой ВМ:
    curl http://localhost:8080/metrics
    # Или с управляющей ВМ:
    curl http://<IP_АДРЕС_ROCKY>:8080/metrics
    ```
    *   Найдите строку `host_info`. Ожидаемый вывод: `host_info{type="virtual_machine"} 1.0`

### Для режима `container`

1.  **Статус службы systemd:**
    ```bash
    sudo systemctl status my_microservice
    ```
    *   Ожидаемый вывод: `Active: inactive (dead)`

2.  **Наличие контейнера:**
    ```bash
    sudo docker ps
    ```
    *   Ожидаемый вывод: Контейнер `my_microservice` *должен* быть в списке запущенных.

3.  **Метрики:** Откройте в браузере или через `curl`:
    ```bash
    # На самой ВМ:
    curl http://localhost:8080/metrics
    # Или с Управляющей ВМ:
    curl http://<IP_АДРЕС_ROCKY>:8080/metrics
    ```
    *   Найдите строку `host_info`. Ожидаемый вывод: `host_info{type="container"} 1.0`

### Для режима `physical`

Эта проверка демонстрирует логику скрипта `app.py`, когда он запускается без явного указания среды через переменную окружения. В этом случае ожидается, что метрика покажет тип `physical`.

1.  Остановите сервис `systemd` или контейнер на целевой ВМ (в зависимости от того, какой режим был активен):
    *   Если был режим `vm`:
        ```bash
        sudo systemctl stop my_microservice
        ```
    *   Если был режим `container`:
        ```bash
        sudo docker stop my_microservice
        ```
2.  Перейдите в директорию приложения на целевой ВМ:
    ```bash
    cd /opt/myapp
    ```
3.  Активируйте виртуальное окружение:
    ```bash
    source venv/bin/activate
    ```
4.  Запустите скрипт вручную:
    ```bash
    python app.py
    ```
5.  В другом терминале (или в браузере) проверьте метрики:
    ```bash
    curl http://localhost:8080/metrics
    ```
    *   Найдите строку `host_info`. Ожидаемый вывод: `host_info{type="physical"} 1.0`

## Примечания

*   **Ошибка "handler '...' not found":** если при первом запуске плейбука возникает ошибка `ERROR! The requested handler 'Reload systemd and restart microservice' was not found...`, то повторно запустите ту же команду `ansible-playbook ...`. Обычно это связано с временными задержками кэша файловой системы или Ansible и решается повторным запуском.
*   **Ошибка "address already in use" при запуске контейнера:** если при переключении с режима `vm` на `container` возникает ошибка о занятом порте 8080, это может означать, что процесс `systemd` не успел полностью освободить порт. Плейбук включает небольшую паузу (`ansible.builtin.pause`) для решения этой проблемы. Если ошибка сохраняется, можно вручную найти и остановить процесс, занимающий порт (с помощью `sudo ss -tulnp | grep ':8080'`, затем `sudo kill <PID>`), и повторить запуск плейбука для режима `container`.
