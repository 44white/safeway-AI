#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/sdp.h>
#include <bluetooth/sdp_lib.h>
#include <bluetooth/rfcomm.h>

// 블루투스 주소 초기화
bdaddr_t bdaddr_any = {0, 0, 0, 0, 0, 0};
bdaddr_t bdaddr_local = {0, 0, 0, 0xff, 0xff, 0xff};

// UUID 문자열을 uuid_t로 변환
int _str2uuid(const char *uuid_str, uuid_t *uuid) {
    uint32_t uuid_int[4];
    char *endptr;
    char buf[9] = {0};

    if (strlen(uuid_str) == 36) {
        if (uuid_str[8] != '-' || uuid_str[13] != '-' || uuid_str[18] != '-' || uuid_str[23] != '-') return 0;
        strncpy(buf, uuid_str, 8);
        uuid_int[0] = htonl(strtoul(buf, &endptr, 16));
        if (endptr != buf + 8) return 0;

        strncpy(buf, uuid_str + 9, 4); strncpy(buf + 4, uuid_str + 14, 4);
        uuid_int[1] = htonl(strtoul(buf, &endptr, 16));
        if (endptr != buf + 8) return 0;

        strncpy(buf, uuid_str + 19, 4); strncpy(buf + 4, uuid_str + 24, 4);
        uuid_int[2] = htonl(strtoul(buf, &endptr, 16));
        if (endptr != buf + 8) return 0;

        strncpy(buf, uuid_str + 28, 8);
        uuid_int[3] = htonl(strtoul(buf, &endptr, 16));
        if (endptr != buf + 8) return 0;

        sdp_uuid128_create(uuid, uuid_int);
    } else if (strlen(uuid_str) == 8) {
        uint32_t i = strtoul(uuid_str, &endptr, 16);
        if (endptr != uuid_str + 8) return 0;
        sdp_uuid32_create(uuid, i);
    } else if (strlen(uuid_str) == 4) {
        int i = strtol(uuid_str, &endptr, 16);
        if (endptr != uuid_str + 4) return 0;
        sdp_uuid16_create(uuid, i);
    } else {
        return 0;
    }
    return 1;
}

// SDP 서비스 등록
sdp_session_t *register_service(uint8_t rfcomm_channel) {
    const char *service_name = "Armatus Bluetooth server";
    const char *svc_dsc = "A HERMIT server that interfaces with the Armatus Android app";
    const char *service_prov = "Armatus";

    uuid_t root_uuid, l2cap_uuid, rfcomm_uuid, svc_uuid, svc_class_uuid;
    sdp_list_t *l2cap_list = 0, *rfcomm_list = 0, *root_list = 0, *proto_list = 0;
    sdp_list_t *access_proto_list = 0, *svc_class_list = 0, *profile_list = 0;
    sdp_data_t *channel = 0;
    sdp_profile_desc_t profile;
    sdp_record_t record = {0};
    sdp_session_t *session = 0;

    _str2uuid("00001101-0000-1000-8000-00805F9B34FB", &svc_uuid);
    sdp_set_service_id(&record, svc_uuid);

    sdp_uuid16_create(&svc_class_uuid, SERIAL_PORT_SVCLASS_ID);
    svc_class_list = sdp_list_append(0, &svc_class_uuid);
    sdp_set_service_classes(&record, svc_class_list);

    sdp_uuid16_create(&profile.uuid, SERIAL_PORT_PROFILE_ID);
    profile.version = 0x0100;
    profile_list = sdp_list_append(0, &profile);
    sdp_set_profile_descs(&record, profile_list);

    sdp_uuid16_create(&root_uuid, PUBLIC_BROWSE_GROUP);
    root_list = sdp_list_append(0, &root_uuid);
    sdp_set_browse_groups(&record, root_list);

    sdp_uuid16_create(&l2cap_uuid, L2CAP_UUID);
    l2cap_list = sdp_list_append(0, &l2cap_uuid);
    proto_list = sdp_list_append(0, l2cap_list);

    sdp_uuid16_create(&rfcomm_uuid, RFCOMM_UUID);
    channel = sdp_data_alloc(SDP_UINT8, &rfcomm_channel);
    rfcomm_list = sdp_list_append(0, &rfcomm_uuid);
    sdp_list_append(rfcomm_list, channel);
    sdp_list_append(proto_list, rfcomm_list);

    access_proto_list = sdp_list_append(0, proto_list);
    sdp_set_access_protos(&record, access_proto_list);

    sdp_set_info_attr(&record, service_name, service_prov, svc_dsc);

    session = sdp_connect(&bdaddr_any, &bdaddr_local, SDP_RETRY_IF_BUSY);
    sdp_record_register(session, &record, 0);

    sdp_data_free(channel);
    sdp_list_free(l2cap_list, 0);
    sdp_list_free(rfcomm_list, 0);
    sdp_list_free(root_list, 0);
    sdp_list_free(access_proto_list, 0);
    sdp_list_free(svc_class_list, 0);
    sdp_list_free(profile_list, 0);

    return session;
}

// 서버 초기화 및 연결 수립
int init_server(int *client_out, sdp_session_t **session_out) {
    int port = 3;
    struct sockaddr_rc loc_addr = {0}, rem_addr = {0};
    socklen_t opt = sizeof(rem_addr);
    char addr_str[18] = {0};

    loc_addr.rc_family = AF_BLUETOOTH;
    loc_addr.rc_bdaddr = bdaddr_any;
    loc_addr.rc_channel = (uint8_t)port;

    *session_out = register_service(port);

    int sock = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (sock < 0) {
        perror("socket");
        return -1;
    }

    if (bind(sock, (struct sockaddr *)&loc_addr, sizeof(loc_addr)) < 0) {
        perror("bind");
        close(sock);
        return -1;
    }

    if (listen(sock, 1) < 0) {
        perror("listen");
        close(sock);
        return -1;
    }

    printf("Waiting for connection...\n");
    int client = accept(sock, (struct sockaddr *)&rem_addr, &opt);
    if (client < 0) {
        perror("accept");
        close(sock);
        return -1;
    }

    ba2str(&rem_addr.rc_bdaddr, addr_str);
    printf("Accepted connection from %s\n", addr_str);
    *client_out = client;
    close(sock);  // 리스닝 소켓 닫기 (클라이언트 하나만 처리하므로)
    return 0;
}

// 메시지 읽기 및 파일 저장
char input[1024] = {0};
char *read_server(int client) {
    int bytes_read = read(client, input, sizeof(input));
    if (bytes_read > 0) {
        input[bytes_read] = '\0';  // 문자열 종료 문자 보장
        printf("Received: [%s]\n", input);

        // 파일에 수신 내용 저장
        FILE *fp = fopen("received_messages.txt", "a");
        if (fp != NULL) {
            fprintf(fp, "%s\n", input);
            fclose(fp);
        } else {
            perror("fopen");
        }

        return input;
    }
    return NULL;
}

// 메시지 보내기
void write_server(int client, const char *message) {
    int bytes_sent = write(client, message, strlen(message));
    if (bytes_sent > 0) {
        printf("Sent: [%s]\n", message);
    }
}

int main() {
    while (1) {
        int client = -1;
        sdp_session_t *session = NULL;

        if (init_server(&client, &session) != 0) {
            fprintf(stderr, "Failed to initialize server. Retrying...\n");
            if (session) sdp_close(session);
            sleep(1);
            continue;
        }

        while (1) {
            char *recv_message = read_server(client);
            if (!recv_message) {
                printf("Client disconnected.\n");
                close(client);
                sdp_close(session);
                break;
            }
            write_server(client, recv_message);
        }
    }

    return 0;
}
