#pragma once
#include <cstddef>
#include <cstdint>
#include <span>

// Design contract only. No socket backend or game hook is implemented here.
namespace pbz::multiplayer {
using PeerId = std::uint64_t;
using EntityId = std::uint64_t;
enum class TransportMode { DirectHost, Relay };
enum class AuthorityMode { Host }; // Relay is a transport, never a combat authority.
enum class Channel { SnapshotUnreliableSequenced, EventReliableOrdered };
enum class MessageKind {
    Join, Welcome, Ready, LoadArena, ArenaLoaded, StartMatch,
    Input, PlayerSnapshot, AttackIntent, CombatResult, HealthState,
    PlayerDied, Respawn, MatchResult, Heartbeat, Leave
};
struct MessageHeader {
    std::uint16_t protocolVersion;
    MessageKind kind;
    std::uint64_t roomId;
    std::uint64_t matchEpoch; // Changes per match; reject stale packets.
    PeerId sender;
    PeerId recipient;
    std::uint64_t sequence;
    std::uint64_t simulationTick;
};
struct RoomRules {
    TransportMode transport;
    AuthorityMode authority = AuthorityMode::Host;
    PeerId host;
    std::uint32_t maxPlayers;
};
// Local types are NOT a wire ABI: encode fields explicitly with bounded lengths,
// fixed endian, authenticated connection identity and version negotiation.
class ITransportEvents {
public:
    virtual ~ITransportEvents() = default;
    virtual void OnConnected(PeerId peer) = 0;
    virtual void OnDisconnected(PeerId peer) = 0;
    virtual void OnMessage(PeerId authenticatedSender, Channel channel,
                           std::span<const std::byte> payload) = 0;
};
class IRoomTransport {
public:
    virtual ~IRoomTransport() = default;
    virtual TransportMode Mode() const = 0;
    virtual void SetEvents(ITransportEvents* sink) = 0;
    virtual bool Send(PeerId recipient, Channel channel,
                      std::span<const std::byte> payload) = 0;
    virtual void Poll() = 0;
    virtual void Close() = 0;
};
// Both adapters implement IRoomTransport. RoomSession and CombatAuthority depend
// only on this interface. DirectHost: guests connect to host; Relay: every peer
// connects to relay, which routes by authenticated room membership and recipient.
} // namespace pbz::multiplayer
