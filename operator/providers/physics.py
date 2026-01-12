"""Physics computation provider using NumPy/SciPy."""

from typing import Any
import numpy as np
from scipy import constants, integrate, optimize

from .base import BaseProvider


class PhysicsProvider(BaseProvider):
    """Provider for physics calculations using NumPy/SciPy."""

    name = "physics"
    provider_type = "compute"
    capabilities = ["physics", "math", "numerical", "scientific"]

    # Physical constants
    CONSTANTS = {
        "c": constants.c,  # Speed of light
        "h": constants.h,  # Planck constant
        "hbar": constants.hbar,  # Reduced Planck constant
        "G": constants.G,  # Gravitational constant
        "e": constants.e,  # Elementary charge
        "m_e": constants.m_e,  # Electron mass
        "m_p": constants.m_p,  # Proton mass
        "k_B": constants.k,  # Boltzmann constant
        "N_A": constants.N_A,  # Avogadro constant
        "R": constants.R,  # Gas constant
        "epsilon_0": constants.epsilon_0,  # Vacuum permittivity
        "mu_0": constants.mu_0,  # Vacuum permeability
        "alpha": constants.alpha,  # Fine structure constant
        "Rydberg": constants.Rydberg,  # Rydberg constant
    }

    def __init__(self):
        super().__init__()
        # Build operation registry
        self._operations = {
            # Quantum mechanics
            "hydrogen_binding_energy": self._hydrogen_binding_energy,
            "hydrogen_wavelength": self._hydrogen_wavelength,
            "de_broglie_wavelength": self._de_broglie_wavelength,
            "uncertainty_principle": self._uncertainty_principle,

            # Relativity
            "time_dilation": self._time_dilation,
            "length_contraction": self._length_contraction,
            "lorentz_factor": self._lorentz_factor,
            "relativistic_mass": self._relativistic_mass,
            "mass_energy": self._mass_energy,

            # Classical mechanics
            "kinetic_energy": self._kinetic_energy,
            "potential_energy": self._potential_energy,
            "orbital_period": self._orbital_period,
            "escape_velocity": self._escape_velocity,

            # Thermodynamics
            "ideal_gas": self._ideal_gas,
            "thermal_energy": self._thermal_energy,

            # Electromagnetism
            "coulomb_force": self._coulomb_force,
            "electric_field": self._electric_field,

            # General
            "get_constant": self._get_constant,
            "evaluate": self._evaluate_expression,
        }

    async def execute(self, query: str, operation: str = None, **kwargs) -> Any:
        """Execute a physics calculation."""
        if operation and operation in self._operations:
            return await self._operations[operation](**kwargs)

        # Try to parse operation from query
        query_lower = query.lower()
        for op_name, op_func in self._operations.items():
            if op_name.replace("_", " ") in query_lower:
                return await op_func(**kwargs)

        return {"error": f"Unknown operation. Available: {list(self._operations.keys())}"}

    async def health_check(self) -> bool:
        """Physics provider is always healthy (local computation)."""
        return True

    # === Quantum Mechanics ===

    async def _hydrogen_binding_energy(self, n: int = 1, **kwargs) -> dict:
        """Calculate hydrogen atom binding energy for quantum number n."""
        # E_n = -13.6 eV / n^2
        E_eV = -13.6 / (n ** 2)
        E_J = E_eV * constants.eV
        return {
            "operation": "hydrogen_binding_energy",
            "n": n,
            "energy_eV": E_eV,
            "energy_J": E_J,
            "formula": "E_n = -13.6 eV / n²",
        }

    async def _hydrogen_wavelength(self, n_initial: int, n_final: int, **kwargs) -> dict:
        """Calculate hydrogen emission/absorption wavelength (Rydberg formula)."""
        # 1/λ = R_H * (1/n_f² - 1/n_i²)
        inv_wavelength = constants.Rydberg * (1 / n_final**2 - 1 / n_initial**2)
        wavelength = 1 / inv_wavelength
        frequency = constants.c / wavelength
        return {
            "operation": "hydrogen_wavelength",
            "n_initial": n_initial,
            "n_final": n_final,
            "wavelength_m": wavelength,
            "wavelength_nm": wavelength * 1e9,
            "frequency_Hz": frequency,
            "formula": "1/λ = R_H × (1/n_f² - 1/n_i²)",
        }

    async def _de_broglie_wavelength(self, mass_kg: float, velocity_ms: float, **kwargs) -> dict:
        """Calculate de Broglie wavelength."""
        # λ = h / (m * v)
        wavelength = constants.h / (mass_kg * velocity_ms)
        return {
            "operation": "de_broglie_wavelength",
            "mass_kg": mass_kg,
            "velocity_ms": velocity_ms,
            "wavelength_m": wavelength,
            "formula": "λ = h / (m × v)",
        }

    async def _uncertainty_principle(self, delta_x: float = None, delta_p: float = None, **kwargs) -> dict:
        """Heisenberg uncertainty principle: Δx × Δp ≥ ℏ/2."""
        min_product = constants.hbar / 2
        if delta_x:
            min_delta_p = min_product / delta_x
            return {
                "operation": "uncertainty_principle",
                "delta_x": delta_x,
                "min_delta_p": min_delta_p,
                "formula": "Δx × Δp ≥ ℏ/2",
            }
        elif delta_p:
            min_delta_x = min_product / delta_p
            return {
                "operation": "uncertainty_principle",
                "delta_p": delta_p,
                "min_delta_x": min_delta_x,
                "formula": "Δx × Δp ≥ ℏ/2",
            }
        return {"min_product": min_product, "formula": "Δx × Δp ≥ ℏ/2"}

    # === Relativity ===

    async def _lorentz_factor(self, velocity_ms: float = None, beta: float = None, **kwargs) -> dict:
        """Calculate Lorentz factor γ."""
        if velocity_ms:
            beta = velocity_ms / constants.c
        gamma = 1 / np.sqrt(1 - beta**2)
        return {
            "operation": "lorentz_factor",
            "beta": beta,
            "velocity_ms": beta * constants.c,
            "gamma": gamma,
            "formula": "γ = 1 / √(1 - β²)",
        }

    async def _time_dilation(self, proper_time: float, velocity_ms: float, **kwargs) -> dict:
        """Calculate time dilation."""
        beta = velocity_ms / constants.c
        gamma = 1 / np.sqrt(1 - beta**2)
        dilated_time = gamma * proper_time
        return {
            "operation": "time_dilation",
            "proper_time": proper_time,
            "velocity_ms": velocity_ms,
            "gamma": gamma,
            "dilated_time": dilated_time,
            "formula": "t = γ × t₀",
        }

    async def _length_contraction(self, proper_length: float, velocity_ms: float, **kwargs) -> dict:
        """Calculate length contraction."""
        beta = velocity_ms / constants.c
        gamma = 1 / np.sqrt(1 - beta**2)
        contracted_length = proper_length / gamma
        return {
            "operation": "length_contraction",
            "proper_length": proper_length,
            "velocity_ms": velocity_ms,
            "gamma": gamma,
            "contracted_length": contracted_length,
            "formula": "L = L₀ / γ",
        }

    async def _relativistic_mass(self, rest_mass_kg: float, velocity_ms: float, **kwargs) -> dict:
        """Calculate relativistic mass."""
        beta = velocity_ms / constants.c
        gamma = 1 / np.sqrt(1 - beta**2)
        rel_mass = gamma * rest_mass_kg
        return {
            "operation": "relativistic_mass",
            "rest_mass_kg": rest_mass_kg,
            "velocity_ms": velocity_ms,
            "gamma": gamma,
            "relativistic_mass_kg": rel_mass,
            "formula": "m = γ × m₀",
        }

    async def _mass_energy(self, mass_kg: float, **kwargs) -> dict:
        """Calculate mass-energy equivalence E = mc²."""
        energy_J = mass_kg * constants.c**2
        energy_eV = energy_J / constants.eV
        return {
            "operation": "mass_energy",
            "mass_kg": mass_kg,
            "energy_J": energy_J,
            "energy_eV": energy_eV,
            "energy_MeV": energy_eV / 1e6,
            "formula": "E = mc²",
        }

    # === Classical Mechanics ===

    async def _kinetic_energy(self, mass_kg: float, velocity_ms: float, **kwargs) -> dict:
        """Calculate kinetic energy."""
        KE = 0.5 * mass_kg * velocity_ms**2
        return {
            "operation": "kinetic_energy",
            "mass_kg": mass_kg,
            "velocity_ms": velocity_ms,
            "kinetic_energy_J": KE,
            "formula": "KE = ½mv²",
        }

    async def _potential_energy(self, mass_kg: float, height_m: float, g: float = 9.81, **kwargs) -> dict:
        """Calculate gravitational potential energy."""
        PE = mass_kg * g * height_m
        return {
            "operation": "potential_energy",
            "mass_kg": mass_kg,
            "height_m": height_m,
            "g": g,
            "potential_energy_J": PE,
            "formula": "PE = mgh",
        }

    async def _orbital_period(self, semi_major_axis_m: float, central_mass_kg: float, **kwargs) -> dict:
        """Calculate orbital period using Kepler's third law."""
        T = 2 * np.pi * np.sqrt(semi_major_axis_m**3 / (constants.G * central_mass_kg))
        return {
            "operation": "orbital_period",
            "semi_major_axis_m": semi_major_axis_m,
            "central_mass_kg": central_mass_kg,
            "period_seconds": T,
            "period_days": T / 86400,
            "formula": "T = 2π√(a³/GM)",
        }

    async def _escape_velocity(self, mass_kg: float, radius_m: float, **kwargs) -> dict:
        """Calculate escape velocity."""
        v_escape = np.sqrt(2 * constants.G * mass_kg / radius_m)
        return {
            "operation": "escape_velocity",
            "mass_kg": mass_kg,
            "radius_m": radius_m,
            "escape_velocity_ms": v_escape,
            "escape_velocity_kms": v_escape / 1000,
            "formula": "v_escape = √(2GM/r)",
        }

    # === Thermodynamics ===

    async def _ideal_gas(self, P: float = None, V: float = None, n: float = None, T: float = None, **kwargs) -> dict:
        """Ideal gas law PV = nRT. Solve for missing variable."""
        R = constants.R
        if P is None:
            P = n * R * T / V
            solved = "P"
        elif V is None:
            V = n * R * T / P
            solved = "V"
        elif n is None:
            n = P * V / (R * T)
            solved = "n"
        elif T is None:
            T = P * V / (n * R)
            solved = "T"
        else:
            solved = "verification"

        return {
            "operation": "ideal_gas",
            "P_Pa": P,
            "V_m3": V,
            "n_mol": n,
            "T_K": T,
            "solved_for": solved,
            "formula": "PV = nRT",
        }

    async def _thermal_energy(self, temperature_K: float, degrees_of_freedom: int = 3, **kwargs) -> dict:
        """Calculate average thermal energy."""
        E = 0.5 * degrees_of_freedom * constants.k * temperature_K
        return {
            "operation": "thermal_energy",
            "temperature_K": temperature_K,
            "degrees_of_freedom": degrees_of_freedom,
            "energy_J": E,
            "energy_eV": E / constants.eV,
            "formula": "E = (f/2)kT",
        }

    # === Electromagnetism ===

    async def _coulomb_force(self, q1: float, q2: float, r: float, **kwargs) -> dict:
        """Calculate Coulomb force between two charges."""
        k = 1 / (4 * np.pi * constants.epsilon_0)
        F = k * q1 * q2 / r**2
        return {
            "operation": "coulomb_force",
            "q1_C": q1,
            "q2_C": q2,
            "r_m": r,
            "force_N": F,
            "formula": "F = kq₁q₂/r²",
        }

    async def _electric_field(self, charge: float, r: float, **kwargs) -> dict:
        """Calculate electric field from a point charge."""
        k = 1 / (4 * np.pi * constants.epsilon_0)
        E = k * charge / r**2
        return {
            "operation": "electric_field",
            "charge_C": charge,
            "r_m": r,
            "E_field_NC": E,
            "formula": "E = kq/r²",
        }

    # === General ===

    async def _get_constant(self, name: str, **kwargs) -> dict:
        """Get a physical constant by name."""
        if name in self.CONSTANTS:
            return {
                "operation": "get_constant",
                "name": name,
                "value": self.CONSTANTS[name],
                "available": list(self.CONSTANTS.keys()),
            }
        return {
            "error": f"Unknown constant: {name}",
            "available": list(self.CONSTANTS.keys()),
        }

    async def _evaluate_expression(self, expression: str, **kwargs) -> dict:
        """Evaluate a mathematical expression with constants available."""
        # Safe evaluation with numpy and constants
        safe_dict = {
            "np": np,
            "pi": np.pi,
            "e": np.e,
            "sqrt": np.sqrt,
            "sin": np.sin,
            "cos": np.cos,
            "tan": np.tan,
            "exp": np.exp,
            "log": np.log,
            "log10": np.log10,
            **self.CONSTANTS,
        }
        try:
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return {
                "operation": "evaluate",
                "expression": expression,
                "result": float(result) if np.isscalar(result) else result.tolist(),
            }
        except Exception as ex:
            return {"error": str(ex), "expression": expression}
