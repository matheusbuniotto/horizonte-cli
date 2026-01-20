import json
import os
from pathlib import Path
from horizonte.core.storage import GoalsRepository, ConfigRepository, CheckinRepository, atomic_write
from horizonte.core.models import Goal, Horizon, SmartCriteria, Config

def test_atomic_write(tmp_path):
    f = tmp_path / "test.txt"
    atomic_write(f, "content1", make_backup=False)
    assert f.read_text() == "content1"
    
    atomic_write(f, "content2", make_backup=True)
    assert f.read_text() == "content2"
    # Check backup exists
    backups = list(tmp_path.glob("test.*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text() == "content1"

def test_goals_repository(tmp_path):
    repo = GoalsRepository(file_path=tmp_path / "goals.json")
    
    # Empty load
    assert repo.load() == []
    
    # Add goal
    goal = Goal(
        title="Test Goal",
        description="Desc",
        horizon=Horizon.SHORT_TERM,
        smart_criteria=SmartCriteria(
            specific="s", measurable="m", achievable="a", relevant="r", time_bound="t"
        )
    )
    repo.add(goal)
    
    # Load
    loaded = repo.load()
    assert len(loaded) == 1
    assert loaded[0].title == "Test Goal"
    assert loaded[0].smart_criteria.specific == "s"

def test_config_repository(tmp_path):
    repo = ConfigRepository(file_path=tmp_path / "config.json")
    
    # Empty load
    config = repo.load()
    assert config.user_name is None
    
    # Save
    config.user_name = "Matheus"
    repo.save(config)
    
    # Load again
    loaded = repo.load()
    assert loaded.user_name == "Matheus"

def test_checkin_repository(tmp_path):
    repo = CheckinRepository(dir_path=tmp_path / "checkins")
    
    # Save checkin
    from horizonte.core.models import CheckIn, CheckInType
    checkin = CheckIn(
        type=CheckInType.MONTHLY,
        goals_covered=[],
        file_path=""
    )
    
    path = repo.save(checkin, "# Review")
    assert path.exists()
    assert "# Review" in path.read_text()
    
    # List
    files = repo.list_all()
    assert len(files) == 1
    assert files[0] == path
