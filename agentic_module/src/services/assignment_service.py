from models import AssetAssignment, Staff

class AssignmentService:

    def __init__(self, db):
        self.db = db

    def get_assignment_with_staff(self, asset_id):

        assignment = (
            self.db.query(AssetAssignment, Staff)
            .join(Staff, Staff.staff_id == AssetAssignment.staff_id)
            .filter(
                AssetAssignment.asset_id == asset_id,
            )
            .first()
        )

        if not assignment:
            return None

        asset_assignment, staff = assignment

        return {
            "staff_id": staff.staff_id,
            "name": staff.full_name,
            "email": staff.email,
            "role": staff.role
        }