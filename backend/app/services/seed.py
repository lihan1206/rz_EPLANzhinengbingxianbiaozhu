import logging

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import Component, Project, User, Wire
from app.services.parallel_analysis import analyze_project_parallel_groups

logger = logging.getLogger(__name__)


def seed_initial_data(db: Session) -> None:
    has_user = db.query(User).first()
    if has_user:
        return

    admin = User(username="admin", password_hash=get_password_hash("admin123"), role="admin")
    engineer = User(username="engineer", password_hash=get_password_hash("engineer123"), role="engineer")
    viewer = User(username="viewer", password_hash=get_password_hash("viewer123"), role="viewer")
    db.add_all([admin, engineer, viewer])
    db.flush()

    project = Project(name="示例电气主控柜", version="v1")
    db.add(project)
    db.flush()

    components = [
        Component(project_id=project.id, name="断路器QF1", type="断路器", terminal="X1", description="主回路保护"),
        Component(project_id=project.id, name="接触器KM1", type="接触器", terminal="X2", description="电机启动"),
        Component(project_id=project.id, name="继电器KA1", type="继电器", terminal="X3", description="控制联锁"),
    ]
    db.add_all(components)

    wires = [
        Wire(
            project_id=project.id,
            number="W-001",
            area=1.5,
            color="黑",
            material="铜",
            length=2.3,
            start_terminal="X1:1",
            end_terminal="X2:1",
            is_shielded=False,
        ),
        Wire(
            project_id=project.id,
            number="W-002",
            area=1.5,
            color="黑",
            material="铜",
            length=2.4,
            start_terminal="X1:1",
            end_terminal="X2:1",
            is_shielded=False,
        ),
        Wire(
            project_id=project.id,
            number="W-003",
            area=1.5,
            color="黑",
            material="铜",
            length=2.2,
            start_terminal="X1:1",
            end_terminal="X2:1",
            is_shielded=False,
        ),
        Wire(
            project_id=project.id,
            number="W-004",
            area=0.75,
            color="黄绿",
            material="铜",
            length=3.1,
            start_terminal="X2:2",
            end_terminal="X3:5",
            is_shielded=True,
        ),
        Wire(
            project_id=project.id,
            number="W-005",
            area=0.75,
            color="黄绿",
            material="铜",
            length=3.0,
            start_terminal="X2:2",
            end_terminal="X3:5",
            is_shielded=True,
        ),
    ]
    db.add_all(wires)
    db.commit()

    analyze_project_parallel_groups(db, project.id, min_parallel_count=2)
    logger.info("种子数据初始化完成")
