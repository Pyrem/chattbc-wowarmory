import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const QUALITY_COLORS: Record<number, string> = {
  0: "text-gray-500", // Poor
  1: "text-white", // Common
  2: "text-green-500", // Uncommon
  3: "text-blue-500", // Rare
  4: "text-purple-500", // Epic
  5: "text-orange-500", // Legendary
};

const SLOT_ORDER = [
  "HEAD",
  "NECK",
  "SHOULDER",
  "BACK",
  "CHEST",
  "SHIRT",
  "TABARD",
  "WRIST",
  "HANDS",
  "WAIST",
  "LEGS",
  "FEET",
  "FINGER_1",
  "FINGER_2",
  "TRINKET_1",
  "TRINKET_2",
  "MAIN_HAND",
  "OFF_HAND",
  "RANGED",
];

const SLOT_LABELS: Record<string, string> = {
  HEAD: "Head",
  NECK: "Neck",
  SHOULDER: "Shoulders",
  BACK: "Back",
  CHEST: "Chest",
  SHIRT: "Shirt",
  TABARD: "Tabard",
  WRIST: "Wrists",
  HANDS: "Hands",
  WAIST: "Waist",
  LEGS: "Legs",
  FEET: "Feet",
  FINGER_1: "Ring 1",
  FINGER_2: "Ring 2",
  TRINKET_1: "Trinket 1",
  TRINKET_2: "Trinket 2",
  MAIN_HAND: "Main Hand",
  OFF_HAND: "Off Hand",
  RANGED: "Ranged",
};

interface EquipItem {
  slot?: { type?: string };
  item?: { id?: number; name?: string };
  name?: string;
  quality?: { type?: string; name?: string };
  level?: { value?: number };
  enchantments?: Array<{ display_string?: string }>;
  sockets?: Array<{ item?: { name?: string } }>;
}

interface GearDisplayProps {
  equipment: Record<string, unknown>;
}

export function GearDisplay({ equipment }: GearDisplayProps) {
  const items = (equipment.equipped_items as EquipItem[] | undefined) ?? [];

  const itemsBySlot = new Map<string, EquipItem>();
  for (const item of items) {
    const slotType = item.slot?.type;
    if (slotType) {
      itemsBySlot.set(slotType, item);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Equipment</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No equipment data available.
          </p>
        ) : (
          <div className="space-y-1">
            {SLOT_ORDER.map((slot) => {
              const item = itemsBySlot.get(slot);
              return <GearSlot key={slot} slot={slot} item={item} />;
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function GearSlot({ slot, item }: { slot: string; item?: EquipItem }) {
  const label = SLOT_LABELS[slot] ?? slot;

  if (!item) {
    return (
      <div className="flex items-center gap-2 rounded px-2 py-1">
        <span className="text-muted-foreground w-24 shrink-0 text-xs">
          {label}
        </span>
        <span className="text-muted-foreground text-sm italic">Empty</span>
      </div>
    );
  }

  const qualityType = item.quality?.type;
  let qualityNum = 1;
  if (qualityType === "POOR") qualityNum = 0;
  if (qualityType === "UNCOMMON") qualityNum = 2;
  if (qualityType === "RARE") qualityNum = 3;
  if (qualityType === "EPIC") qualityNum = 4;
  if (qualityType === "LEGENDARY") qualityNum = 5;

  const colorClass = QUALITY_COLORS[qualityNum] ?? "text-white";
  const itemName = item.name ?? item.item?.name ?? "Unknown Item";
  const ilvl = item.level?.value;
  const enchant = item.enchantments?.[0]?.display_string;
  const gems = item.sockets?.map((s) => s.item?.name).filter(Boolean);

  return (
    <div className="group hover:bg-muted/50 flex items-start gap-2 rounded px-2 py-1">
      <span className="text-muted-foreground w-24 shrink-0 text-xs leading-5">
        {label}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className={`text-sm font-medium ${colorClass}`}>
            {itemName}
          </span>
          {ilvl && (
            <span className="text-muted-foreground text-xs">ilvl {ilvl}</span>
          )}
        </div>
        {(enchant ?? (gems && gems.length > 0)) && (
          <div className="text-muted-foreground flex flex-wrap gap-2 text-xs">
            {enchant && <span className="text-green-400">{enchant}</span>}
            {gems?.map((gem, i) => (
              <span key={i} className="text-blue-400">
                {gem}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
