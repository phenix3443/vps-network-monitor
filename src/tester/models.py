#!/usr/bin/env python3

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class PingResult:
    success: bool
    min: Optional[float] = None
    max: Optional[float] = None
    avg: Optional[float] = None
    median: Optional[float] = None
    packet_loss: float = 0.0
    samples: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MtrHop:
    hop: int
    ip: str
    sent: Optional[int] = None
    last: Optional[float] = None
    avg: Optional[float] = None
    best: Optional[float] = None
    worst: Optional[float] = None
    loss: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MtrResult:
    success: bool
    hops: List[MtrHop] = field(default_factory=list)
    total_hops: int = 0
    destination: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["hops"] = [hop.to_dict() for hop in self.hops]
        return result


@dataclass
class VPSTestResult:
    timestamp: str
    name: str
    provider: str
    region: str
    ip: str
    ping: PingResult
    mtr: Optional[MtrResult] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["ping"] = self.ping.to_dict()
        if self.mtr:
            result["mtr"] = self.mtr.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VPSTestResult":
        ping_data = data.get("ping", {})
        ping = PingResult(**ping_data)

        mtr = None
        if "mtr" in data and data["mtr"]:
            mtr_data = data["mtr"]
            hops = [MtrHop(**hop) for hop in mtr_data.get("hops", [])]
            mtr = MtrResult(
                success=mtr_data.get("success", False),
                hops=hops,
                total_hops=mtr_data.get("total_hops", 0),
                destination=mtr_data.get("destination"),
                error=mtr_data.get("error"),
            )

        return cls(
            timestamp=data["timestamp"],
            name=data["name"],
            provider=data["provider"],
            region=data["region"],
            ip=data["ip"],
            ping=ping,
            mtr=mtr,
        )


@dataclass
class TestSession:
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    total_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    results: List[VPSTestResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["results"] = [r.to_dict() for r in self.results]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestSession":
        results = [VPSTestResult.from_dict(r) for r in data.get("results", [])]
        return cls(
            session_id=data["session_id"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            total_tests=data.get("total_tests", 0),
            successful_tests=data.get("successful_tests", 0),
            failed_tests=data.get("failed_tests", 0),
            results=results,
        )
