from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.resource import ResourceGroup, Resource
from app.enums import ResourceType
from app.schemas.group import GroupNode, GroupReorderItem


def get_groups_by_type(
    db: Session, 
    resource_type: int, 
    source_id: Optional[int] = None,
    exclude_default: bool = False
) -> List[ResourceGroup]:
    query = db.query(ResourceGroup).filter(ResourceGroup.resource_type == resource_type)
    if source_id is not None:
        query = query.filter(ResourceGroup.source_id == source_id)
    if exclude_default:
        query = query.filter(ResourceGroup.is_default == 0)
    return query.order_by(ResourceGroup.sort_order, ResourceGroup.id).all()


def build_tree(groups: List[ResourceGroup]) -> List[GroupNode]:
    group_map = {g.id: GroupNode(
        id=g.id,
        name=g.name,
        parent_id=g.parent_id,
        level=g.level,
        real_path=g.real_path,
        sort_order=g.sort_order,
        is_default=g.is_default,
        children=[]
    ) for g in groups}

    root_nodes = []
    for g in groups:
        node = group_map[g.id]
        if g.parent_id is None:
            root_nodes.append(node)
        elif g.parent_id in group_map:
            group_map[g.parent_id].children.append(node)
        else:
            root_nodes.append(node)

    return root_nodes


def get_group_tree(
    db: Session, 
    resource_type: int, 
    source_id: Optional[int] = None,
    exclude_default: bool = False
) -> Tuple[List[GroupNode], str]:
    groups = get_groups_by_type(db, resource_type, source_id, exclude_default)
    tree = build_tree(groups)
    type_name = ResourceType(resource_type).name
    return tree, type_name


def get_group_by_id(db: Session, group_id: int) -> Optional[ResourceGroup]:
    return db.query(ResourceGroup).filter(ResourceGroup.id == group_id).first()


def get_next_sort_order(db: Session, parent_id: Optional[int], resource_type: int, source_id: Optional[int] = None) -> int:
    query = db.query(func.max(ResourceGroup.sort_order)).filter(
        ResourceGroup.resource_type == resource_type
    )
    if source_id is not None:
        query = query.filter(ResourceGroup.source_id == source_id)
    if parent_id is None:
        query = query.filter(ResourceGroup.parent_id.is_(None))
    else:
        query = query.filter(ResourceGroup.parent_id == parent_id)
    result = query.scalar()
    return (result or -1) + 1


def create_group(db: Session, resource_type: int, name: str, parent_id: Optional[int] = None, source_id: Optional[int] = None) -> ResourceGroup:
    if parent_id is None:
        existing_root = db.query(ResourceGroup).filter(
            ResourceGroup.resource_type == resource_type,
            ResourceGroup.source_id == source_id,
            ResourceGroup.parent_id.is_(None)
        ).first()
        if existing_root:
            raise ValueError("该来源下已存在默认分组")
    
    if parent_id:
        parent = get_group_by_id(db, parent_id)
        if not parent:
            raise ValueError(f"Parent group {parent_id} not found")
        level = parent.level + 1
        real_path = f"{parent.real_path}/{name}"
        is_default = 0
    else:
        level = 0
        real_path = name
        is_default = 1 if name == "默认分组" else 0

    sort_order = get_next_sort_order(db, parent_id, resource_type, source_id)

    group = ResourceGroup(
        resource_type=resource_type,
        source_id=source_id,
        name=name,
        parent_id=parent_id,
        level=level,
        real_path=real_path,
        sort_order=sort_order,
        is_default=is_default,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def update_group(db: Session, group_id: int, name: str) -> Optional[ResourceGroup]:
    group = get_group_by_id(db, group_id)
    if not group:
        return None

    old_name = group.name
    group.name = name

    if group.parent_id is None:
        group.real_path = name
    else:
        parent = get_group_by_id(db, group.parent_id)
        if parent:
            group.real_path = f"{parent.real_path}/{name}"

    _update_children_paths(db, group_id, old_name, name)
    db.commit()
    db.refresh(group)
    return group


def _update_children_paths(db: Session, parent_id: int, old_name: str, new_name: str):
    children = db.query(ResourceGroup).filter(ResourceGroup.parent_id == parent_id).all()
    for child in children:
        child.real_path = child.real_path.replace(f"/{old_name}/", f"/{new_name}/")
        if child.real_path.endswith(f"/{old_name}"):
            child.real_path = child.real_path[:-len(old_name)] + new_name
        _update_children_paths(db, child.id, old_name, new_name)


def _get_all_descendant_ids(db: Session, group_id: int) -> List[int]:
    children = db.query(ResourceGroup).filter(ResourceGroup.parent_id == group_id).all()
    ids = []
    for child in children:
        ids.append(child.id)
        ids.extend(_get_all_descendant_ids(db, child.id))
    return ids


def get_descendants_resource_count(db: Session, group_id: int) -> int:
    all_ids = _get_all_descendant_ids(db, group_id)
    all_ids.insert(0, group_id)
    return db.query(Resource).filter(Resource.group_id.in_(all_ids)).count()


def delete_group(db: Session, group_id: int) -> bool:
    group = get_group_by_id(db, group_id)
    if not group:
        return False

    if group.is_default == 1:
        raise ValueError("不能删除默认分组")

    all_group_ids = _get_all_descendant_ids(db, group_id)
    all_group_ids.insert(0, group_id)

    default_group = db.query(ResourceGroup).filter(
        ResourceGroup.source_id == group.source_id,
        ResourceGroup.resource_type == group.resource_type,
        ResourceGroup.is_default == 1
    ).first()

    if not default_group:
        default_group = create_group(
            db,
            group.resource_type,
            "默认分组",
            parent_id=None,
            source_id=group.source_id
        )

    db.query(Resource).filter(Resource.group_id.in_(all_group_ids)).update(
        {Resource.group_id: default_group.id},
        synchronize_session=False
    )

    db.query(ResourceGroup).filter(ResourceGroup.id.in_(all_group_ids)).delete(
        synchronize_session=False
    )

    db.commit()
    return True


def move_group(db: Session, group_id: int, new_parent_id: Optional[int], new_sort_order: Optional[int]) -> Optional[ResourceGroup]:
    group = get_group_by_id(db, group_id)
    if not group:
        return None

    if group.id == new_parent_id:
        raise ValueError("Cannot move group to itself")

    old_real_path = group.real_path
    old_level = group.level

    if new_parent_id:
        parent = get_group_by_id(db, new_parent_id)
        if not parent:
            raise ValueError(f"Target parent group {new_parent_id} not found")
        _check_cycle(db, group_id, new_parent_id)
        group.parent_id = new_parent_id
        group.level = parent.level + 1
        group.real_path = f"{parent.real_path}/{group.name}"
    else:
        group.parent_id = None
        group.level = 0
        group.real_path = group.name

    if new_sort_order is not None:
        group.sort_order = new_sort_order

    _update_children_paths_and_levels(db, group_id, old_real_path, group.real_path, old_level, group.level)

    db.commit()
    db.refresh(group)
    return group


def _check_cycle(db: Session, group_id: int, target_parent_id: int):
    current = target_parent_id
    while current:
        if current == group_id:
            raise ValueError("Cannot move group to its own descendant")
        parent_group = get_group_by_id(db, current)
        if not parent_group:
            break
        current = parent_group.parent_id


def _update_children_paths_and_levels(db: Session, parent_id: int, old_path: str, new_path: str, old_level: int, new_level: int):
    children = db.query(ResourceGroup).filter(ResourceGroup.parent_id == parent_id).all()
    level_delta = new_level - old_level
    for child in children:
        child.real_path = child.real_path.replace(old_path, new_path, 1)
        child.level += level_delta
        _update_children_paths_and_levels(db, child.id, old_path, new_path, old_level, new_level)


def reorder_groups(db: Session, items: List[GroupReorderItem]) -> bool:
    for item in items:
        group = get_group_by_id(db, item.id)
        if group:
            group.sort_order = item.sort_order
    db.commit()
    return True