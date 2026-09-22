#include "XPLMDataAccess.h"
#include "XPLMPlugin.h"
#include "XPLMProcessing.h"
#include "XPLMUtilities.h"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#if IBM
  #define WIN32_LEAN_AND_MEAN
  #include <winsock2.h>
  #include <ws2tcpip.h>
  using socket_t = SOCKET;
  constexpr socket_t INVALID_SOCKET_VALUE = INVALID_SOCKET;
#else
  #include <arpa/inet.h>
  #include <fcntl.h>
  #include <netinet/in.h>
  #include <sys/socket.h>
  #include <unistd.h>
  using socket_t = int;
  constexpr socket_t INVALID_SOCKET_VALUE = -1;
#endif

namespace {
constexpr int kPort = 49075;
constexpr std::size_t kMaxPacket = 1024;
constexpr std::size_t kMaxSubscriptions = 96;
constexpr int kMaxPacketsPerFrame = 32;
constexpr double kPublishIntervalSec = 0.10; // 10 Hz state publication.
constexpr int kMaxActionsPerSecond = 12;

socket_t g_socket = INVALID_SOCKET_VALUE;
sockaddr_in g_lastClient{};
bool g_hasClient = false;
std::string g_token = "dev-token-change-me";
std::vector<std::string> g_allowedCommandPrefixes{"sim/", "laminar/B738/"};
std::vector<std::string> g_allowedDatarefPrefixes{"sim/", "laminar/B738/"};
std::chrono::steady_clock::time_point g_lastPublish = std::chrono::steady_clock::now();
std::deque<std::chrono::steady_clock::time_point> g_actionTimes;

struct Subscription {
    std::string key;
    std::string path;
    XPLMDataRef ref = nullptr;
    XPLMDataTypeID type = xplmType_Unknown;
    int arrayIndex = -1;
};

std::unordered_map<std::string, Subscription> g_subscriptions;

void debug(const std::string& message) {
    const std::string line = "[B737AICopilot] " + message + "\n";
    XPLMDebugString(line.c_str());
}

std::vector<std::string> split(const std::string& text, char delim) {
    std::vector<std::string> result;
    std::stringstream stream(text);
    std::string item;
    while (std::getline(stream, item, delim)) {
        result.push_back(item);
    }
    return result;
}

std::vector<std::string> envPrefixes(const char* name, std::vector<std::string> fallback) {
    const char* raw = std::getenv(name);
    if (!raw || std::strlen(raw) == 0) return fallback;
    std::vector<std::string> out;
    for (const auto& item : split(raw, ',')) {
        if (!item.empty()) out.push_back(item);
    }
    return out.empty() ? fallback : out;
}

bool startsWithAllowedPrefix(const std::string& value, const std::vector<std::string>& prefixes) {
    return std::any_of(prefixes.begin(), prefixes.end(), [&](const std::string& p) {
        return value.rfind(p, 0) == 0;
    });
}

bool safeField(const std::string& value) {
    if (value.empty() || value.size() > 240) return false;
    return value.find('|') == std::string::npos && value.find('\n') == std::string::npos && value.find('\r') == std::string::npos;
}

void closeSocket() {
    if (g_socket == INVALID_SOCKET_VALUE) return;
#if IBM
    closesocket(g_socket);
#else
    close(g_socket);
#endif
    g_socket = INVALID_SOCKET_VALUE;
}

bool setNonBlocking(socket_t sock) {
#if IBM
    u_long mode = 1;
    return ioctlsocket(sock, FIONBIO, &mode) == 0;
#else
    const int flags = fcntl(sock, F_GETFL, 0);
    return flags >= 0 && fcntl(sock, F_SETFL, flags | O_NONBLOCK) == 0;
#endif
}

bool initSocket() {
#if IBM
    WSADATA wsa{};
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        debug("WSAStartup failed");
        return false;
    }
#endif
    g_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (g_socket == INVALID_SOCKET_VALUE) {
        debug("socket() failed");
        return false;
    }

    int reuse = 1;
    setsockopt(g_socket, SOL_SOCKET, SO_REUSEADDR, reinterpret_cast<const char*>(&reuse), sizeof(reuse));

    sockaddr_in local{};
    local.sin_family = AF_INET;
    local.sin_port = htons(kPort);
    inet_pton(AF_INET, "127.0.0.1", &local.sin_addr);
    if (bind(g_socket, reinterpret_cast<sockaddr*>(&local), sizeof(local)) != 0) {
        debug("bind(127.0.0.1:49075) failed");
        closeSocket();
        return false;
    }
    if (!setNonBlocking(g_socket)) {
        debug("failed to make UDP socket non-blocking");
        closeSocket();
        return false;
    }
    debug("UDP bridge listening on 127.0.0.1:49075");
    return true;
}

void sendToClient(const std::string& text) {
    if (!g_hasClient || g_socket == INVALID_SOCKET_VALUE || text.size() > kMaxPacket) return;
    sendto(g_socket, text.c_str(), static_cast<int>(text.size()), 0,
           reinterpret_cast<const sockaddr*>(&g_lastClient), sizeof(g_lastClient));
}

void sendError(const std::string& reason) {
    sendToClient("ERR|" + reason);
}

bool tokenValid(const std::vector<std::string>& fields, std::size_t tokenIndex = 1) {
    return fields.size() > tokenIndex && fields[tokenIndex] == g_token;
}

double nowSeconds() {
    using namespace std::chrono;
    return duration<double>(steady_clock::now().time_since_epoch()).count();
}

long long unixMillis() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
}

bool actionRateAllowed() {
    const auto now = std::chrono::steady_clock::now();
    while (!g_actionTimes.empty() && std::chrono::duration<double>(now - g_actionTimes.front()).count() > 1.0) {
        g_actionTimes.pop_front();
    }
    if (static_cast<int>(g_actionTimes.size()) >= kMaxActionsPerSecond) return false;
    g_actionTimes.push_back(now);
    return true;
}

void handleSubscribe(const std::vector<std::string>& f) {
    if (f.size() != 4 || !tokenValid(f)) {
        sendError("bad_sub_packet");
        return;
    }
    const std::string& key = f[2];
    const std::string& path = f[3];
    if (!safeField(key) || !safeField(path)) {
        sendError("bad_sub_field");
        return;
    }
    if (!startsWithAllowedPrefix(path, g_allowedDatarefPrefixes)) {
        sendError("dataref_prefix_denied");
        return;
    }
    if (g_subscriptions.size() >= kMaxSubscriptions && g_subscriptions.find(key) == g_subscriptions.end()) {
        sendError("subscription_limit");
        return;
    }
    std::string lookupPath = path;
    int arrayIndex = -1;
    const auto left = path.rfind('[');
    if (left != std::string::npos && path.back() == ']') {
        try {
            arrayIndex = std::stoi(path.substr(left + 1, path.size() - left - 2));
            lookupPath = path.substr(0, left);
        } catch (...) {
            sendError("bad_array_index:" + key);
            return;
        }
    }
    XPLMDataRef ref = XPLMFindDataRef(lookupPath.c_str());
    if (!ref) {
        sendError("dataref_not_found:" + key);
        return;
    }
    const XPLMDataTypeID type = XPLMGetDataRefTypes(ref);
    const bool scalar = (type & (xplmType_Int | xplmType_Float | xplmType_Double)) != 0;
    const bool array = arrayIndex >= 0 && (type & (xplmType_IntArray | xplmType_FloatArray)) != 0;
    if (!scalar && !array) {
        sendError("unsupported_dataref_type:" + key);
        return;
    }
    g_subscriptions[key] = Subscription{key, path, ref, type, arrayIndex};
    sendToClient("ACK|SUB|" + key);
}

void handleAction(const std::vector<std::string>& f) {
    if (f.size() != 3 || !tokenValid(f)) {
        sendError("bad_act_packet");
        return;
    }
    const std::string& commandName = f[2];
    if (!safeField(commandName) || !startsWithAllowedPrefix(commandName, g_allowedCommandPrefixes)) {
        sendError("command_prefix_denied");
        return;
    }
    if (!actionRateAllowed()) {
        sendError("action_rate_limited");
        return;
    }
    XPLMCommandRef cmd = XPLMFindCommand(commandName.c_str());
    if (!cmd) {
        sendError("command_not_found");
        return;
    }
    XPLMCommandOnce(cmd);
    sendToClient("ACK|ACT|" + commandName);
}

void handlePacket(const char* data, std::size_t len, const sockaddr_in& sender) {
    if (len == 0 || len > kMaxPacket) return;
    if (sender.sin_addr.s_addr != htonl(INADDR_LOOPBACK)) return;

    g_lastClient = sender;
    g_hasClient = true;

    std::string text(data, len);
    const auto fields = split(text, '|');
    if (fields.empty()) return;

    const std::string& verb = fields[0];
    if (verb == "HELLO") {
        if (!tokenValid(fields)) {
            sendError("auth_failed");
            return;
        }
        sendToClient("READY|" + std::to_string(unixMillis()));
    } else if (verb == "SUB") {
        handleSubscribe(fields);
    } else if (verb == "ACT") {
        handleAction(fields);
    } else if (verb == "PING") {
        if (!tokenValid(fields)) {
            sendError("auth_failed");
            return;
        }
        sendToClient("PONG|" + std::to_string(unixMillis()));
    } else {
        sendError("unknown_verb");
    }
}

void pollSocket() {
    if (g_socket == INVALID_SOCKET_VALUE) return;
    for (int i = 0; i < kMaxPacketsPerFrame; ++i) {
        std::array<char, kMaxPacket + 1> buffer{};
        sockaddr_in sender{};
#if IBM
        int senderLen = sizeof(sender);
#else
        socklen_t senderLen = sizeof(sender);
#endif
        const int received = recvfrom(g_socket, buffer.data(), static_cast<int>(kMaxPacket), 0,
                                      reinterpret_cast<sockaddr*>(&sender), &senderLen);
        if (received <= 0) break;
        handlePacket(buffer.data(), static_cast<std::size_t>(received), sender);
    }
}

void publishValues() {
    if (!g_hasClient) return;
    const auto now = std::chrono::steady_clock::now();
    if (std::chrono::duration<double>(now - g_lastPublish).count() < kPublishIntervalSec) return;
    g_lastPublish = now;

    for (const auto& [key, sub] : g_subscriptions) {
        double value = 0.0;
        if (sub.arrayIndex >= 0 && (sub.type & xplmType_FloatArray)) {
            float item = 0.0f;
            if (XPLMGetDatavf(sub.ref, &item, sub.arrayIndex, 1) != 1) continue;
            value = item;
        } else if (sub.arrayIndex >= 0 && (sub.type & xplmType_IntArray)) {
            int item = 0;
            if (XPLMGetDatavi(sub.ref, &item, sub.arrayIndex, 1) != 1) continue;
            value = static_cast<double>(item);
        } else if (sub.type & xplmType_Double) {
            value = XPLMGetDatad(sub.ref);
        } else if (sub.type & xplmType_Float) {
            value = XPLMGetDataf(sub.ref);
        } else if (sub.type & xplmType_Int) {
            value = static_cast<double>(XPLMGetDatai(sub.ref));
        } else {
            continue;
        }
        std::ostringstream out;
        out.precision(10);
        out << "VAL|" << key << '|' << value;
        sendToClient(out.str());
    }
}

float flightLoop(float, float, int, void*) {
    pollSocket();
    publishValues();
    return -1.0f;
}

} // namespace

PLUGIN_API int XPluginStart(char* outName, char* outSignature, char* outDescription) {
    std::strcpy(outName, "B737 AI Copilot Bridge");
    std::strcpy(outSignature, "ai.openai.reference.b737copilot.bridge");
    std::strcpy(outDescription, "Local IPC bridge for a bilingual Boeing 737 AI copilot.");

    if (const char* token = std::getenv("B737_COPILOT_TOKEN"); token && std::strlen(token) >= 12) {
        g_token = token;
    } else {
        debug("WARNING: using development token; set B737_COPILOT_TOKEN (>=12 chars) before production use");
    }
    g_allowedCommandPrefixes = envPrefixes("B737_COPILOT_ALLOWED_COMMAND_PREFIXES", g_allowedCommandPrefixes);
    g_allowedDatarefPrefixes = envPrefixes("B737_COPILOT_ALLOWED_DATAREF_PREFIXES", g_allowedDatarefPrefixes);

    if (!initSocket()) return 0;
    XPLMRegisterFlightLoopCallback(flightLoop, -1.0f, nullptr);
    return 1;
}

PLUGIN_API void XPluginStop(void) {
    XPLMUnregisterFlightLoopCallback(flightLoop, nullptr);
    g_subscriptions.clear();
    closeSocket();
#if IBM
    WSACleanup();
#endif
}

PLUGIN_API int XPluginEnable(void) {
    return 1;
}

PLUGIN_API void XPluginDisable(void) {
}

PLUGIN_API void XPluginReceiveMessage(XPLMPluginID, int, void*) {
}
