"""
Servicio para la lógica de negocio de progreso de peso de usuarios
"""
from fastapi import HTTPException
from app.models.UserProgression import WeightProgress
from app.repositories.progression_repository import ProgressionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.progression_schema import WeightProgressCreate, WeightProgressSummary


class ProgressionService:
	"""Servicio para gestionar el progreso histórico de peso de un usuario."""

	def __init__(self, repository: ProgressionRepository, user_repository: UserRepository):
		self.repository = repository
		self.user_repository = user_repository

	def register_weight(self, user_id: int, progress_data: WeightProgressCreate) -> WeightProgress:
		user = self.user_repository.get_by_id(user_id)
		if user is None:
			raise HTTPException(status_code=404, detail="User not found")

		new_entry = WeightProgress(user_id=user_id, weight=progress_data.weight)
		created_entry = self.repository.create(new_entry)

		# Sincroniza el peso actual del usuario para consultas rápidas.
		user.weight = progress_data.weight
		self.user_repository.update(user)

		return created_entry

	def get_user_progress(self, user_id: int) -> list[WeightProgress]:
		user = self.user_repository.get_by_id(user_id)
		if user is None:
			raise HTTPException(status_code=404, detail="User not found")

		return self.repository.get_by_user_id(user_id)

	def get_progress_summary(self, user_id: int) -> WeightProgressSummary:
		user = self.user_repository.get_by_id(user_id)
		if user is None:
			raise HTTPException(status_code=404, detail="User not found")

		progress_entries = self.repository.get_by_user_id(user_id)
		if not progress_entries:
			return WeightProgressSummary(
				user_id=user_id,
				target_weight=user.target_weight,
				initial_weight=None,
				current_weight=user.weight,
				weight_change=None,
				entries_count=0,
				on_track=None,
				trend=None,
			)

		initial_weight = progress_entries[0].weight
		current_weight = progress_entries[-1].weight
		weight_change = current_weight - initial_weight

		on_track = None
		trend = None
		if user.target_weight is not None:
			initial_distance = abs(initial_weight - user.target_weight)
			current_distance = abs(current_weight - user.target_weight)
			on_track = current_distance <= initial_distance

			if current_distance < initial_distance:
				trend = "mejorando"
			elif current_distance > initial_distance:
				trend = "empeorando"
			else:
				trend = "sin_cambios"

		return WeightProgressSummary(
			user_id=user_id,
			target_weight=user.target_weight,
			initial_weight=initial_weight,
			current_weight=current_weight,
			weight_change=weight_change,
			entries_count=len(progress_entries),
			on_track=on_track,
			trend=trend,
		)
