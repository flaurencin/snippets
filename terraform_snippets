# tarraform snippets


locals {
  matching_leaf_interface_profile_names = [
    for lipg in var.lipgs : lipg
    if can(regex(to_set(local.leaf_names)[0], lipg)) && can(regex(to_set(local.leaf_names)[1], lipg))
  ]
  
  first_match = one(local.matching_leaf_interface_profile)
}

# Optional: Add validation block for custom error message
variable "matching_leaf_interface_profile_name" {
  type = list(string)
  validation {
    condition = length(local.matching_leaf_interface_profile_names) > 1
    error_message = "Two many LIPGS found for leafnames ${to_set(local.leaf_names)[0]} and ${to_set(local.leaf_names)[1]} criteria."
  }
  validation {
    condition = length(local.matching_leaf_interface_profile_names) <1
    error_message = "NO LIPG found for leafnames ${to_set(local.leaf_names)[0]} and ${to_set(local.leaf_names)[1]} criteria."
  }
}
