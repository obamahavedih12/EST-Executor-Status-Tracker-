from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import datetime


class ExecutorStatus(Enum):
    UPDATED  = "🟢 Updated"
    UPDATING = "🟡 Updating"
    DETECTED = "🔴 Detected"
    UNKNOWN  = "⚪ Unknown"


@dataclass
class ExecutorResult:
    name:            str
    version:         str
    platform:        str
    cost:            str
    free:            bool
    status:          ExecutorStatus
    detected:        bool
    unc_status:      bool
    update_status:   bool
    unc_percentage:  Optional[int]  = None
    sunc_percentage: Optional[int]  = None
    decompiler:      Optional[bool] = None
    multi_inject:    Optional[bool] = None
    key_system:      Optional[bool] = None
    website_link:    Optional[str]  = None
    discord_link:    Optional[str]  = None
    purchase_link:   Optional[str]  = None
    updated_date:    Optional[str]  = None
    rbx_version:     Optional[str]  = None
    fetched_at:      datetime.datetime = field(
                         default_factory=datetime.datetime.utcnow
                     )

    @staticmethod
    def from_api(data: dict) -> "ExecutorResult":
        update_status = data.get("updateStatus", False)
        detected      = data.get("detected", False)

        if not update_status:
            status = ExecutorStatus.UPDATING
        elif detected:
            status = ExecutorStatus.DETECTED
        else:
            status = ExecutorStatus.UPDATED

        return ExecutorResult(
            name            = data.get("title", "Unknown"),
            version         = data.get("version", "N/A"),
            platform        = data.get("platform", "N/A"),
            cost            = data.get("cost", "Free" if data.get("free") else "N/A"),
            free            = data.get("free", False),
            status          = status,
            detected        = detected,
            unc_status      = data.get("uncStatus", False),
            update_status   = update_status,
            unc_percentage  = data.get("uncPercentage"),
            sunc_percentage = data.get("suncPercentage"),
            decompiler      = data.get("decompiler"),
            multi_inject    = data.get("multiInject"),
            key_system      = data.get("keysystem"),
            website_link    = data.get("websitelink"),
            discord_link    = data.get("discordlink"),
            purchase_link   = data.get("purchaselink"),
            updated_date    = data.get("updatedDate"),
            rbx_version     = data.get("rbxversion"),
        )

    def to_embed_field(self) -> dict:
        lines = [self.status.value]
        if self.unc_percentage  is not None:
            lines.append(f"UNC: `{self.unc_percentage}%`")
        if self.sunc_percentage is not None:
            lines.append(f"sUNC: `{self.sunc_percentage}%`")
        lines.append(f"Version: `{self.version}`")
        lines.append(f"Cost: `{self.cost}`")
        if self.updated_date:
            lines.append(f"Updated: `{self.updated_date}`")
        return {"name": self.name, "value": "\n".join(lines), "inline": True}


@dataclass
class StatusReport:
    results:      list[ExecutorResult]
    generated_at: datetime.datetime = field(
                      default_factory=datetime.datetime.utcnow
                  )

    @property
    def updated_count(self)  -> int:
        return sum(1 for r in self.results if r.status == ExecutorStatus.UPDATED)

    @property
    def updating_count(self) -> int:
        return sum(1 for r in self.results if r.status == ExecutorStatus.UPDATING)

    @property
    def detected_count(self) -> int:
        return sum(1 for r in self.results if r.status == ExecutorStatus.DETECTED)
