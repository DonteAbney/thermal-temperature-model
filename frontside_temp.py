from scipy import constants
import math


def tempatureFront(
    fourthDependence, tau, t_wall, k, epsilon_f, epsilon_b, a_area, z, p_max, t_b
):
    if fourthDependence == True:
        a = (tau * constants.Stefan_Boltzmann * (epsilon_b - epsilon_f)) / k
        d = -1
        e = (
            ((tau * constants.Stefan_Boltzmann * (t_wall**4)) / k)
            * (epsilon_f - epsilon_b)
            - ((tau * z * p_max) / (a_area * k))
            + t_b
        )

        q = -1 / a
        r = e / a

        y_cubed_term = q**2 / 2
        sqrt_term = math.sqrt(abs((q**4 / 4) - (64 * r**3) / 27))

        if (q**4 / 4) - (64 * r**3) / 27 >= 0:
            y1 = math.cbrt(y_cubed_term + sqrt_term) + math.cbrt(
                y_cubed_term - sqrt_term
            )
        else:
            complex_cube_1 = complex(y_cubed_term, sqrt_term) ** (1 / 3)
            complex_cube_2 = complex(y_cubed_term, -sqrt_term) ** (1 / 3)
            y1 = (complex_cube_1 + complex_cube_2).real

        roots = []

        discriminant_pos = y1 - 2 * (y1 / 2 + q / (2 * math.sqrt(y1)))
        if discriminant_pos >= 0:
            root1 = (math.sqrt(y1) + math.sqrt(discriminant_pos)) / 2
            root2 = (math.sqrt(y1) - math.sqrt(discriminant_pos)) / 2
            if root1 > 0:
                roots.append(root1)
            if root2 > 0:
                roots.append(root2)

        discriminant_neg = y1 - 2 * (y1 / 2 - q / (2 * math.sqrt(y1)))
        if discriminant_neg >= 0:
            root3 = (-math.sqrt(y1) + math.sqrt(discriminant_neg)) / 2
            root4 = (-math.sqrt(y1) - math.sqrt(discriminant_neg)) / 2
            if root3 > 0:
                roots.append(root3)
            if root4 > 0:
                roots.append(root4)

        return roots

    else:
        t_f = t_b - ((2 * tau) / (a_area * k)) * (
            p_max * z - constants.Stefan_Boltzmann * a_area * epsilon_b * (t_b**4)
        )
        return [t_f]
