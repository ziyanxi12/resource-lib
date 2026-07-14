"""
初始化分组数据脚本
创建示例分组，并更新 JSON 文件中的 group_id
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.resource import ResourceGroup
from app.enums import ResourceType


def init_groups():
    db = SessionLocal()
    
    groups_to_create = [
        # 图标分组
        {"resource_type": ResourceType.icon, "name": "系统"},
        {"resource_type": ResourceType.icon, "name": "导航"},
        {"resource_type": ResourceType.icon, "name": "A领域"},
        # 插画分组
        {"resource_type": ResourceType.illus, "name": "空状态"},
        {"resource_type": ResourceType.illus, "name": "反馈"},
    ]
    
    created_groups = {}
    
    for g in groups_to_create:
        existing = db.query(ResourceGroup).filter(
            ResourceGroup.resource_type == g["resource_type"],
            ResourceGroup.name == g["name"]
        ).first()
        
        if existing:
            print(f"分组已存在: {g['name']} (ID={existing.id}, type={g['resource_type']})")
            created_groups[f"{g['resource_type']}_{g['name']}"] = existing.id
        else:
            group = ResourceGroup(
                resource_type=g["resource_type"],
                name=g["name"],
                level=0,
                real_path=g["name"],
                sort_order=0
            )
            db.add(group)
            db.flush()
            print(f"创建分组: {g['name']} (ID={group.id}, type={g['resource_type']})")
            created_groups[f"{g['resource_type']}_{g['name']}"] = group.id
    
    db.commit()
    db.close()
    
    print("\n分组 ID 映射:")
    for key, id in created_groups.items():
        print(f"  {key}: {id}")
    
    return created_groups


if __name__ == "__main__":
    init_groups()